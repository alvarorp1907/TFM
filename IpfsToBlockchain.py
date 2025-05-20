import requests
import subprocess
import os
import time

#constants
DIR_FILES = "/home/alvarorp19/archivesTestingIPFS"
DIR_HYPERLEDGER_NET = "/home/alvarorp19/fabric-samples/test-network"

DIR_CERT_CA_ORG1 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
DIR_CERT_CA_ORG2 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
DIR_CERT_CA_ORDERER =f"{DIR_HYPERLEDGER_NET}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"

CHAINCODE_NAME = "chaincode"
CHAINCODE_CHANNEL = "mychannel"

INVOKE_CN_BASE_CMD = r"peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com " \
                     f"--tls --cafile {DIR_CERT_CA_ORDERER} -C {CHAINCODE_CHANNEL} -n {CHAINCODE_NAME} " \
                     f"--peerAddresses localhost:7051 --tlsRootCertFiles {DIR_CERT_CA_ORG1} " \
                     f"--peerAddresses localhost:9051 --tlsRootCertFiles {DIR_CERT_CA_ORG2} -c"
                     
QUERY_CN_BASE_CMD = f"peer chaincode query -C {CHAINCODE_CHANNEL} -n {CHAINCODE_NAME} -c"

#variables
#IPFS
fileIPFSCID = "0"
fileIPFS = f"{DIR_FILES}/prueba5.txt"

#Stage 1 -> upload file to IPFS through local API server

#add fileIPFS to IPFS
fileIPFSJson = {'fileIPFS': open(fileIPFS, 'rb')}
response = requests.post('http://127.0.0.1:5001/api/v0/add', files=fileIPFSJson)

#checking respose status from local API server
if response.status_code == 200:
    payload = response.json()
    fileIPFSCID = payload['Hash']
    print(f"File named as {fileIPFS} successfully uploaded to IPFS.")
    print(f"{fileIPFS} CID: {fileIPFSCID}")
    print(f"Public URL: https://ipfs.io/ipfs/{fileIPFSCID}")
else:
    print(f"File name as {fileIPFS} cannot be uploaded to IPFS")
    print(f"Error code {response.status_code} received from local API server")
    exit()

#stage 2 -> invoke the chaincode installed in the hyperledger Fabric network to store the file's CID

#Hyperledger Fabric commands
HyperledgerCmd = {"InitLedger"   : INVOKE_CN_BASE_CMD + " \'{\"Args\":[\"InitLedger\"]}\'",
                  "AddNewAsset"  : INVOKE_CN_BASE_CMD + " \'{\"Args\":[\"AddNewAsset\"," + f"\"{fileIPFS}\",\"{fileIPFSCID}\"]" + "}\'",
                  "GetAllAssets" : QUERY_CN_BASE_CMD + " \'{\"Args\":[\"GetAllAssets\"]}\'"}

os.chdir(DIR_HYPERLEDGER_NET)

#ToDo : set environment variables before invoking the chaincode
res = subprocess.run(HyperledgerCmd["AddNewAsset"], capture_output=True, text=True, shell=True)
cleanRes = res.stderr.strip(' \n\r')
transactionStatusCode = cleanRes[-3:]
#time.sleep(2)
#res2 = subprocess.run(HyperledgerCmd["GetAllAssets"], capture_output=True, text=True, shell=True)
if (transactionStatusCode == "200"):
    print(f"CID successfully stored in Hyperledger Fabric Blockchain")
else:
    print(f"Error invoking the chaincode in Hyperledger Fabric Blockchain: {res}")




