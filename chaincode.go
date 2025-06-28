package main

import (
    "log"
	"encoding/json"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

//constants
const FILE_ASSET_TYPE = "fileAsset"
const DEVICE_CONFIG_ASSET_TYPE = "deviceConfigAsset"

// SmartContract provides functions for managing an Asset
type CIDContract struct {
	contractapi.Contract
}

//Asset structure containing the following fields:
//AssetType
//FileName of the file stored in IPFS
//CID of the file
//timestamp
type CIDRecord struct {

	AssetType string `json:"AssetType"`
	FileName string `json:"fileName"`
	CID      string `json:"cid"`
	Timestamp string `json:"timestamp"`
}

//Asset structure containing the following fields:
//name: name of the device
//AssetType
//IP : IP address of the device
//MAC : MAC address of the device
//description : description of the device
type DeviceConfig struct {

	AssetType string `json:"AssetType"`
	Name string `json:"name"`
	IP      string `json:"ip"`
	MAC string `json:"mac"`
	Description string `json:"description"`

}

// InitLedger adds a base set of assets to the ledger
func (c *CIDContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	records := []DeviceConfig{
		{AssetType: DEVICE_CONFIG_ASSET_TYPE, Name: "Gateway", IP: "192.168.1.36", MAC : "00:1A:2B:3C:4D:5E", Description : "Gateway of the network responsible for aggregating all data emitted by waspmotes and storing it in Hyperledger Fabric and IPFS"},
	}

	for _, record := range records {
		data, err := json.Marshal(record)
		if err != nil {
			return err
		}
		
		err = ctx.GetStub().PutState(record.Name, data)
		if err != nil {
			return fmt.Errorf("failed to put to World State %s: %v", record.Name, err)
		}
	}
	
	return nil
}

//function to get a specific device configuration from world state
func (c *CIDContract) GetInfoDevice(ctx contractapi.TransactionContextInterface, deviceName string) (*DeviceConfig, error) {
	data, err := ctx.GetStub().GetState(deviceName)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if data == nil {
		return nil, fmt.Errorf("the asset %s does not exist",deviceName)
	}
	
	var asset DeviceConfig
	err = json.Unmarshal(data, &asset)

	if err != nil {
		return nil, err
	}

	if asset.AssetType != DEVICE_CONFIG_ASSET_TYPE{
		return nil, fmt.Errorf("the asset %s is not a registered device inside the sensor network",deviceName)
	}
	
	return &asset, nil
}

//function that returns all assets found in world state
func (c *CIDContract) GetAllAssets(ctx contractapi.TransactionContextInterface) (string, error) {
	// range query with empty string for startKey and endKey does an
	// open-ended query of all assets in the chaincode namespace.
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return "", err
	}
	defer resultsIterator.Close()

	var resultString string

	for resultsIterator.HasNext() {
		
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return "", err
		}

		resultString += fmt.Sprintf("%s\n\r", string(queryResponse.Value))

	}

	return resultString, nil
}

//function that returns true when asset with given fileExist exists in world state, otherwise false
func (c *CIDContract) FileIPFSExists(ctx contractapi.TransactionContextInterface, cid string) (bool, error) {
	assetJSON, err := ctx.GetStub().GetState(cid)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	if assetJSON == nil {
		return false, nil
	}

	var asset CIDRecord
	err = json.Unmarshal(assetJSON, &asset)
	if err != nil {
		return false, err
	}

	if asset.AssetType != FILE_ASSET_TYPE {
		return false, fmt.Errorf("the asset %s exists but it's not an IPFS file!!", cid)
	}

	return true, nil
}


//function to create a new asset in the World State containing the filename and CID stored in IPFS
func (c *CIDContract) AddNewFileIPFS(ctx contractapi.TransactionContextInterface, fileName string, cid string, timestamp string) error {



	if fileName == "" || cid == "" {
	return fmt.Errorf("fileName and cid cannot be empty")
	}


	exists, err := c.FileIPFSExists(ctx, cid)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the asset %s exists in the ledger", cid)
	}
	
	record := CIDRecord{
		AssetType: FILE_ASSET_TYPE,
		FileName: fileName,
		CID:      cid,
		Timestamp: timestamp,
	}

	data, err := json.Marshal(record)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(cid, data)
}

//function to read an existing file stored in the World State
func (c *CIDContract) GetInfoFileIPFS(ctx contractapi.TransactionContextInterface, cid string) (*CIDRecord, error) {
	exists, err := c.FileIPFSExists(ctx, cid)
	if err != nil {
		return nil, err
	}
	if !exists {
		return nil, fmt.Errorf("the asset %s doesn't exist in the ledger", cid)
	}

	data, err := ctx.GetStub().GetState(cid)

	if err != nil {
		return nil, err
	}

	if data == nil {
   		return nil, fmt.Errorf("the asset %s doesn't exist in the ledger", cid)
	}

	var asset CIDRecord
	err = json.Unmarshal(data, &asset)

	if err != nil {
		return nil, err
	}

	return &asset, nil
}


// function that deletes an given asset from the world state.
func (c *CIDContract) DeleteFileIPFS(ctx contractapi.TransactionContextInterface, cid string) error {
	exists, err := c.FileIPFSExists(ctx, cid)
	if err != nil {
		return err
	}
	if !exists {
		return fmt.Errorf("the asset %s does not exist", cid)
	}

	return ctx.GetStub().DelState(cid)
}


func main() {
	chaincode, err := contractapi.NewChaincode(new(CIDContract))
	if err != nil {
		log.Panicf("Error creating CIDContract chaincode: %v", err)
	}
	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting the chaincode: %v", err.Error())
	}
}