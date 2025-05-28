import requests
import subprocess
import os
import sys
import time
from multiprocessing import Process
from pathlib import Path
import json
from daemonClass import daemon
import datetime
import socket
import re

#################### constants ####################

#relevant directories
DIR_FILES = "/home/alvarorp19/archivesTestingIPFS"
DIR_HYPERLEDGER_NET = "/home/alvarorp19/fabric-samples/test-network"
DIR_HYPERLEDGER_FABRIC_SAMPLES = "/home/alvarorp19/fabric-samples"

DIR_CERT_CA_ORG1 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
DIR_CERT_CA_ORG2 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
DIR_CERT_CA_ORDERER =f"{DIR_HYPERLEDGER_NET}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
DIR_MSP_PEER_ORG1_CONF = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"

#Hyperledger Fabric information
CHAINCODE_NAME = "chaincode"
CHAINCODE_CHANNEL = "mychannel"

#Hyperledger Fabric commands
INVOKE_CN_BASE_CMD = r"peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com " \
                     f"--tls --cafile {DIR_CERT_CA_ORDERER} -C {CHAINCODE_CHANNEL} -n {CHAINCODE_NAME} " \
                     f"--peerAddresses localhost:7051 --tlsRootCertFiles {DIR_CERT_CA_ORG1} " \
                     f"--peerAddresses localhost:9051 --tlsRootCertFiles {DIR_CERT_CA_ORG2} -c"
                     
QUERY_CN_BASE_CMD = f"peer chaincode query -C {CHAINCODE_CHANNEL} -n {CHAINCODE_NAME} -c"

CID_CODE_ERROR = "-1"

#TCP server information
SERVER_MAX_NUMBER_CONNECTIONS = 5
SERVER_PORT = 4000
SERVER_HOST = "0.0.0.0"
RX_BUFFER_LEN = 1024

#################### variables and structures ####################

HyperledgerCmd = {"InitLedger"   : INVOKE_CN_BASE_CMD + " \'{\"Args\":[\"InitLedger\"]}\'",
                  "AddNewAsset"  : INVOKE_CN_BASE_CMD + " \'{{\"Args\":[\"AddNewAsset\"," + "\"{0}\",\"{1}\",\"{2}\"]" + "}}\'",
                  "GetAllAssets" : QUERY_CN_BASE_CMD + " \'{\"Args\":[\"GetAllAssets\"]}\'",
                  "GetInfoAsset" : QUERY_CN_BASE_CMD + " \'{{\"Args\":[\"GetInfoAsset\"," + "\"{0}\"]" + "}}\'"}
                  
HyperledgerEnvVar = {"FABRIC_CFG_PATH" : f"{DIR_HYPERLEDGER_FABRIC_SAMPLES}/config/",
                     "CORE_PEER_TLS_ENABLED" : "true",
                     "CORE_PEER_LOCALMSPID"  : "Org1MSP",
                     "CORE_PEER_TLS_ROOTCERT_FILE" : DIR_CERT_CA_ORG1,
                     "CORE_PEER_MSPCONFIGPATH" : DIR_MSP_PEER_ORG1_CONF,
                     "CORE_PEER_ADDRESS": "localhost:7051"}


#################### MonitoringForIpfsHyperledger class ####################


class MonitoringForIpfsHyperledger(daemon):
    
    #gateway events
    GATEWAY_STORE_CID_EVENT = "STORE_CID"

    def __init__(self,pidFile,debugLevel):
        """
        Class constructor
        """
        super().__init__(pidFile,debugLevel) #constructor
        
        self.server = None #TCP server socket 
        self.gateway = None #TCP gateway socket
        
        #getaway event dictionary:  
        #key = command name | 1st value: command pattern , 2nd value : associated function pointer  
        self.gatewayEventDict = {self.GATEWAY_STORE_CID_EVENT : [fr"{self.GATEWAY_STORE_CID_EVENT} ([a-zA-Z0-9_]+) ([a-zA-Z0-9_]+)", self.uploadCIDtoHyperledger]}
        
        
    
    def uploadFileToIPFS(self,file):
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
    
    
    
    def isIPFfileStoredInHyperledger(self,cidToCheck):
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
        
        res = subprocess.run(HyperledgerCmd["GetInfoAsset"].format(cidToCheck), capture_output=True, text=True, shell=True)
        stdout = res.stdout
        
        if stdout != "":
            dictInfoFile = json.loads(stdout)
            print(f"obtained dict from Hyperledger -> {dictInfoFile}")
            CidReadHyperledger = dictInfoFile["cid"]
            if cidToCheck == CidReadHyperledger:
                print("Nothing to store")
                ret = True
                
        return ret
    
    
    
    def uploadFileToHyperledgerFabric(self,fileName,cid,timestamp):
        """
        Def:
            Function to upload a file to Hyperledger Fabric Blockchain.
        Args:
            targetFile : full path of the file.
            cid : IPFS CID
            timeStamp : Unix time
        Return:
            True if operation is successfully done otherwise False.
        Note:
            None
        """
        #formatting unix time
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        fmtTimestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        #invoking chaincode
        res = subprocess.run(HyperledgerCmd["AddNewAsset"].format(fileName,cid,fmtTimestamp), capture_output=True, text=True, shell=True)
        cleanRes = res.stderr.strip(' \n\r')
        transactionStatusCode = cleanRes[-3:]
        
        if (transactionStatusCode == "200"):
            print(f"CID '{cid}' successfully stored in Hyperledger Fabric Blockchain")
        else:
            print(f"Error invoking the chaincode in Hyperledger Fabric Blockchain: {res}")
    
    
    
    def waitUntilGatewayIsConnected(self):
      """
      Function that waits until a TCP connection is established with the target gateway.
      
      Args:
          None.
          
      Return:
          None.
          
      Note:
          This function reject all clients except the target gateway device. 
      """
      gatewayIsConnected = False
      gatewayIp = "127.0.0.1" #ToDo: fetch this info in Hyperledger fabric
      
      #creating a TCP socket
      self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      #setting options
      self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      #binding IP with port
      self.server.bind((SERVER_HOST, SERVER_PORT))
      #waiting for connection
      self.server.listen(SERVER_MAX_NUMBER_CONNECTIONS)
      
      print("Waiting until gateway is connected...")
      
      while(not gatewayIsConnected):
        #program is blocked here until a connection is established
        clientSocket, clientAddress = self.server.accept()
        clientIp , clientPort = clientAddress
        #checking client
        if clientIp == gatewayIp:
          gatewayIsConnected = True
          self.gateway = clientSocket
        else:
          print("No legitime connection, closing connection...")
          clientSocket.close()
      #once the target connection has been established,
      #can stop listening server port
      print("Connection established with gateway!")
      self.server.close()



    def isSocketClosed(self):
      """
      This function detects whether the gateway socket is closed or not.
      
      Args:
          None
          
      Return:
          Bool
      """
      try:
          # this will try to read bytes without blocking and also without removing them from buffer (peek only)
          data = self.gateway.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
          if len(data) == 0:
              return True
      except BlockingIOError:
          return False  # socket is open and reading from it would block
      except ConnectionResetError:
          return True  # socket was closed for some other reason
      except Exception as e:
          print("unexpected exception when checking if a socket is closed")
          return False
      return False          
   


    def uploadCIDtoHyperledger(self,cmdArgs):
        """
        Upload file to Hyperledger Fabric.
        
        Args:
            cid : IPFS CID to upload.
            filename : filename
            
        Return:
            None
        """
        cid = cmdArgs[0]
        filename = cmdArgs[1]
        unixTime = time.time()
        
        #checking if we need to summit modifications to IPFS and blockchain
        isCidStored = self.isIPFfileStoredInHyperledger(cid)
        if isCidStored == False:
            #upload IPFS file to Hyperledger Fabric
            print(f"Uploading info from file '{filename}' to Hyperledger Fabric!")
            self.uploadFileToHyperledgerFabric(filename,cid,unixTime)
        else:
            print(f"CID '{cid} has been previously stored in Hyperledger'")
    
    
    
    def filesMonitoring(self):
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
        #isFirstIteration = True
        #lastFileModified = ""#path of the last file modified
        #lastTimeStamp = 0 #timeStamp of the last file modified
        #targetDir = Path(DIR_FILES)
        
        #set environment variables before executing any operation in Hyperledger
        for environVarName, environVarValue in HyperledgerEnvVar.items():
            os.environ[environVarName] = environVarValue
            
        self.waitUntilGatewayIsConnected()
        
        while True:
            
            #wait until some gateway event arrives
            rawData = self.gateway.recv(RX_BUFFER_LEN)
            recvData = rawData.decode()
            
            #verify if gateway connection still open
            isConnectionClosed = self.isSocketClosed()
            
            if isConnectionClosed:#closed
                self.waitUntilGatewayIsConnected()
            else:#open
              #processing received data from gateway
              print(f"RECV -> {recvData}")
              cmdNameRcv = recvData.split()[0]
              cmdParamsTuple = tuple()
              
              for cmdName, value in self.gatewayEventDict.items():
                  if cmdNameRcv == cmdName:
                      #check received msg structure
                      pattern = value[0]
                      match = re.search(pattern,recvData)
                      if match:
                        cmdParamsTuple = match.groups()
                        print(cmdParamsTuple)
                        ptrFunction = value[1]
                        ptrFunction(cmdParamsTuple)
                      break
    
    
    
    def run(self):
        """
        Def:
            Deamon routine to be executed in a background process.
        Args:
            Void.
        Return:
            Void.   
        Note:
            None.
        """
        self.filesMonitoring()

        
     
#################### main ####################

if __name__ == "__main__":
    
    if len(sys.argv) == 3:
    
        debugLevel = None
        
        #analyzing 3rd arg
        match sys.argv[2]:
            case "debugOn":
                debugLevel = True
            case "debugOff":
                debugLevel = False
            case _:
                print("The 3rd program argument is unknown")
                sys.exit(2)
                
        daemon = MonitoringForIpfsHyperledger('/home/alvarorp19/scriptsPyTFM/daemon_IPFS_Hyperledger.pid',debugLevel)
        
        #analyzing 2nd arg
        match sys.argv[1]:
            case "start":
                daemon.start()
            case "stop":
                daemon.stop()
            case "restart":
                daemon.restart()
            case _:
                print("The 2nd program argument is unknown")
                sys.exit(2)
        sys.exit(0)
    else:
        print(f"usage: {sys.argv[0]} start|stop|restart debugOn|debugOff")
        sys.exit(2) 