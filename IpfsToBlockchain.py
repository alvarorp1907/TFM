import requests
import subprocess
import os

#constants
LOCAL_DIR_FILES = "/home/alvarorp19/archivesTestingIPFS"
LOCAL_DIR_HYPERLEDGER_TEST_NET = r"/home/alvarorp19/fabric-samples/test-network"

#variables
#IPFS
fileIPFSCID = None
fileIPFS = f"{LOCAL_DIR_FILES}/prueba.txt"

#Hyperledger Fabric
HyperledgerCmd = {"InitLedger" : r"peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile " \
                  r"/home/alvarorp19/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C mychannel -n chaincode " \
                  r"--peerAddresses localhost:7051 --tlsRootCertFiles /home/alvarorp19/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt " \
                  r"--peerAddresses localhost:9051 --tlsRootCertFiles /home/alvarorp19/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt " \
                  "-c \'{\"Args\":[\"InitLedger\"]}\'"}

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

os.chdir(LOCAL_DIR_HYPERLEDGER_TEST_NET)

#ToDo : set environment variables before invoking the chaincode
res = subprocess.run(HyperledgerCmd["InitLedger"], capture_output=True, text=True, shell=True)

print(res)
#ToDo: check status code from chaincode




