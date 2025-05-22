import requests
import subprocess
import os
import time
from multiprocessing import Process
from pathlib import Path
import json

#################### constants ####################

DIR_FILES = "/home/alvarorp19/archivesTestingIPFS"
DIR_HYPERLEDGER_NET = "/home/alvarorp19/fabric-samples/test-network"
DIR_HYPERLEDGER_FABRIC_SAMPLES = "/home/alvarorp19/fabric-samples"

DIR_CERT_CA_ORG1 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
DIR_CERT_CA_ORG2 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
DIR_CERT_CA_ORDERER =f"{DIR_HYPERLEDGER_NET}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
DIR_MSP_PEER_ORG1_CONF = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"

CHAINCODE_NAME = "chaincode"
CHAINCODE_CHANNEL = "mychannel"

INVOKE_CN_BASE_CMD = r"peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com " \
                     f"--tls --cafile {DIR_CERT_CA_ORDERER} -C {CHAINCODE_CHANNEL} -n {CHAINCODE_NAME} " \
                     f"--peerAddresses localhost:7051 --tlsRootCertFiles {DIR_CERT_CA_ORG1} " \
                     f"--peerAddresses localhost:9051 --tlsRootCertFiles {DIR_CERT_CA_ORG2} -c"
                     
QUERY_CN_BASE_CMD = f"peer chaincode query -C {CHAINCODE_CHANNEL} -n {CHAINCODE_NAME} -c"

CID_CODE_ERROR = "-1"

#################### variables and structures ####################

HyperledgerCmd = {"InitLedger"   : INVOKE_CN_BASE_CMD + " \'{\"Args\":[\"InitLedger\"]}\'",
                  "AddNewAsset"  : INVOKE_CN_BASE_CMD + " \'{{\"Args\":[\"AddNewAsset\"," + "\"{0}\",\"{1}\"]" + "}}\'",
                  "GetAllAssets" : QUERY_CN_BASE_CMD + " \'{\"Args\":[\"GetAllAssets\"]}\'",
                  "GetInfoAsset" : QUERY_CN_BASE_CMD + " \'{{\"Args\":[\"GetInfoAsset\"," + "\"{0}\"]" + "}}\'"}
                  
HyperledgerEnvVar = {"FABRIC_CFG_PATH" : f"{DIR_HYPERLEDGER_FABRIC_SAMPLES}/config/",
                     "CORE_PEER_TLS_ENABLED" : "true",
                     "CORE_PEER_LOCALMSPID"  : "Org1MSP",
                     "CORE_PEER_TLS_ROOTCERT_FILE" : DIR_CERT_CA_ORG1,
                     "CORE_PEER_MSPCONFIGPATH" : DIR_MSP_PEER_ORG1_CONF,
                     "CORE_PEER_ADDRESS": "localhost:7051"}


#################### functions ####################


def uploadFileToIPFS(file):
    """
    Def:
        Function to upload a file to IPFS.
    Args:
        targetFile : full path of the file.
    Return:
        Tuple containing the request status and IPFS CID obtained.
    Note:
        None
    """
    retStatus = True
    fileIPFSCID = CID_CODE_ERROR
    fileIPFSJson = {'fileIPFS': open(file, 'rb')}
    
    response = requests.post('http://127.0.0.1:5001/api/v0/add', files=fileIPFSJson)

    #checking respose status from local API server
    if response.status_code == 200:
        payload = response.json()
        fileIPFSCID = payload['Hash']
        print(f"File named as {file} successfully uploaded to IPFS.")
        print(f"{file} CID: {fileIPFSCID}")
        print(f"Public URL: https://ipfs.io/ipfs/{fileIPFSCID}")
    else:
        print(f"File name as {file} cannot be uploaded to IPFS")
        print(f"Error code {response.status_code} received from local API server")
        retStatus = False
      
    return retStatus,fileIPFSCID



def filesMonitoring():
    """
    Def:
        Function to monitor if a new file has been added in the directory where target
        files must be stored
    Args:
        Void 
    Return:
        Void   
    Note:
        This function is executed in a background process
    """
    isFirstIteration = True
    lastFileModified = ""#path of the last file modified
    lastTimeStamp = 0 #timeStamp of the last file modified
    targetDir = Path(DIR_FILES)
    
    #set environment variables before any operation in Hyperledger
    for environVarName, environVarValue in HyperledgerEnvVar.items():
        os.environ[environVarName] = environVarValue
    
    while True:
        #analyzing target file where IPFS file are being stored
        #print(f"Last modification in IPFS dir -> {lastTimeStamp}")
        
        for file in targetDir.iterdir():
            if file.is_file():
                currTimestamp = file.stat().st_mtime
                #print(f"{file.name} → última modificación: {currTimestamp}")
                if lastTimeStamp < currTimestamp:
                    #updating last modified file info
                    lastTimeStamp = currTimestamp
                    lastFileModified = file.name
                    fullPathFile = f"{DIR_FILES}/{lastFileModified}"
                    #if is the first iteration we dont do any operation
                    #in IPFS and Hyperledger
                    if isFirstIteration == False:
                        print(f"File {lastFileModified} has been modified in target directory : {DIR_FILES}")
                        #uploading last modifications to IPFS
                        status,cid = uploadFileToIPFS(fullPathFile)
                        
                        if status:
                            #checking if we need to summit modifications to IPFS and blockchain
                            isCidStored = isIPFfileStoredInHyperledger(fullPathFile,cid)
                            if isCidStored == False:
                                #upload IPFS file to Hyperledger Fabric
                                print(f"Uploading info from file '{fullPathFile}' to Hyperledger Fabric!")
                                uploadFileToHyperledgerFabric(fullPathFile,cid)
                            else:
                                print(f"CID '{cid} has been previously stored in Hyperledger'")
                        
        isFirstIteration = False           
        time.sleep(5)



def isIPFfileStoredInHyperledger(targetFile,cidToCheck):
    """
    Def:
        Function to check if the file specified at first parameter
        is stored in Hyperledger Fabric or not.
    Args:
        targetFile : full path of the target file
    Return:
        True if found otherwise False   
    Note:
        None
    """
    ret = False
    
    res = subprocess.run(HyperledgerCmd["GetInfoAsset"].format(targetFile), capture_output=True, text=True, shell=True)
    stdout = res.stdout
    
    if stdout != "":
        dictInfoFile = json.loads(stdout)
        print(f"obtained dict from Hyperledger -> {dictInfoFile}")
        CidReadHyperledger = dictInfoFile["cid"]
        # print(dictInfoFile["cid"])
        if cidToCheck == CidReadHyperledger:
            print("Nothing to store")
            ret = True
            
    return ret



def uploadFileToHyperledgerFabric(fileName,cid):
    """
    Def:
        Function to upload a file to Hyperledger Fabric Blockchain.
    Args:
        targetFile : full path of the file.
        cid : IPFS CID
    Return:
        True if operation is successfully done otherwise False.
    Note:
        None
    """
    res = subprocess.run(HyperledgerCmd["AddNewAsset"].format(fileName,cid), capture_output=True, text=True, shell=True)
    cleanRes = res.stderr.strip(' \n\r')
    transactionStatusCode = cleanRes[-3:]
    
    if (transactionStatusCode == "200"):
        print(f"CID '{cid}' successfully stored in Hyperledger Fabric Blockchain")
    else:
        print(f"Error invoking the chaincode in Hyperledger Fabric Blockchain: {res}")



#################### main ####################

if __name__ == "__main__":
    filesMonitoring()