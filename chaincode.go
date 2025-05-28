package main

import (
    "log"
	"encoding/json"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

// SmartContract provides functions for managing an Asset
type CIDContract struct {
	contractapi.Contract
}

//Asset structure containing the following fields:
// 1º FileName of the file stored in IPFS
// 2º CID of the file
type CIDRecord struct {
	FileName string `json:"fileName"`
	CID      string `json:"cid"`
	Timestamp string `json:"timestamp"`
}

// InitLedger adds a base set of assets to the ledger
func (c *CIDContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	records := []CIDRecord{
		{FileName: "test1.txt", CID: "QmABC123", Timestamp : "2006-01-02 15:04:05"},
		{FileName: "test2.txt", CID: "QmDEF456", Timestamp : "2006-01-02 15:04:05"},
	}

	for _, record := range records {
		data, err := json.Marshal(record)
		if err != nil {
			return err
		}
		
		err = ctx.GetStub().PutState(record.CID, data)
		if err != nil {
			return fmt.Errorf("failed to put to World State %s: %v", record.FileName, err)
		}
	}
	
	return nil
}

//function to create a new asset in the World State containing the filename and CID stored in IPFS
func (c *CIDContract) AddNewAsset(ctx contractapi.TransactionContextInterface, fileName string, cid string, timestamp string) error {
	//exists, err := c.AssetExists(ctx, fileName)
	//if err != nil {
		//return err
	//}
	//if exists {
		//return fmt.Errorf("the asset %s already exists", fileName)
	//}
	
	record := CIDRecord{
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
func (c *CIDContract) GetInfoAsset(ctx contractapi.TransactionContextInterface, cid string) (*CIDRecord, error) {
	data, err := ctx.GetStub().GetState(cid)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if data == nil {
		return nil, fmt.Errorf("the asset %s does not exist",cid)
	}
	
	var asset CIDRecord
	err = json.Unmarshal(data, &asset)
	if err != nil {
		return nil, err
	}
	
	return &asset, nil
}

//function that returns all assets found in world state
func (c *CIDContract) GetAllAssets(ctx contractapi.TransactionContextInterface) ([]*CIDRecord, error) {
	// range query with empty string for startKey and endKey does an
	// open-ended query of all assets in the chaincode namespace.
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var assets []*CIDRecord
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var asset CIDRecord
		err = json.Unmarshal(queryResponse.Value, &asset)
		if err != nil {
			return nil, err
		}
		assets = append(assets, &asset)
	}

	return assets, nil
}

//function that returns true when asset with given fileExist exists in world state
func (c *CIDContract) AssetExists(ctx contractapi.TransactionContextInterface, cid string) (bool, error) {
	assetJSON, err := ctx.GetStub().GetState(cid)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return assetJSON != nil, nil
}

// function that deletes an given asset from the world state.
func (c *CIDContract) DeleteAsset(ctx contractapi.TransactionContextInterface, cid string) error {
	exists, err := c.AssetExists(ctx, cid)
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