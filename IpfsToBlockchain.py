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
import http.server
import ssl

#################### constants ####################

#relevant directories
DIR_FILES = "/home/alvarorp19/archivesTestingIPFS"
DIR_HYPERLEDGER_NET = "/home/alvarorp19/fabric-samples/test-network"
DIR_HYPERLEDGER_FABRIC_SAMPLES = "/home/alvarorp19/fabric-samples"

DIR_CERT_CA_ORG1 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
DIR_CERT_CA_ORG2 = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
DIR_CERT_CA_ORDERER =f"{DIR_HYPERLEDGER_NET}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"
DIR_MSP_PEER_ORG1_CONF = f"{DIR_HYPERLEDGER_NET}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"

DIR_TARGER_FOLDER_MFS = "/WaterTelemetry"

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

#project directory where certs are stored
CERTS_DIR = "/home/alvarorp19/scriptsPyTFM/"
#certificates directories
CERT_SERVER_DIR = "./serverCertificates+/"
CERT_CA_DIR = "./CAcertificates/"

#HTTPS server information
LOCALHOST = "192.168.1.44"
SERVER_MAX_NUMBER_CONNECTIONS = 5
SERVER_PORT = 5000
RX_BUFFER_LEN = 2048

BLOCKCHAIN_OPERATION_COMPLETED = "SUCESS"
BLOCKCHAIN_OPERATION_FAILED = "FAILURE"

OPERATION_COMPLETED_STATUS_CODE = "200"
OPERATION_FAILED_STATUS_CODE = "500"


#################### variables and structures ####################

HyperledgerCmd = {"InitLedger"   : INVOKE_CN_BASE_CMD + " \'{\"Args\":[\"InitLedger\"]}\'",
                  "AddNewFileIPFS"  : INVOKE_CN_BASE_CMD + " \'{{\"Args\":[\"AddNewFileIPFS\"," + "\"{0}\",\"{1}\",\"{2}\"]" + "}}\'",
                  "GetAllAssets" : QUERY_CN_BASE_CMD + " \'{\"Args\":[\"GetAllAssets\"]}\'",
                  "GetInfoFileIPFS" : QUERY_CN_BASE_CMD + " \'{{\"Args\":[\"GetInfoFileIPFS\"," + "\"{0}\"]" + "}}\'",
                  "GetInfoDevice" : QUERY_CN_BASE_CMD + " \'{{\"Args\":[\"GetInfoDevice\"," + "\"{0}\"]" + "}}\'"}
                  
HyperledgerEnvVar = {"FABRIC_CFG_PATH" : f"{DIR_HYPERLEDGER_FABRIC_SAMPLES}/config/",
                     "CORE_PEER_TLS_ENABLED" : "true",
                     "CORE_PEER_LOCALMSPID"  : "Org1MSP",
                     "CORE_PEER_TLS_ROOTCERT_FILE" : DIR_CERT_CA_ORG1,
                     "CORE_PEER_MSPCONFIGPATH" : DIR_MSP_PEER_ORG1_CONF,
                     "CORE_PEER_ADDRESS": "localhost:7051"}
                     
                     
####################            Functions               ####################
    
    
    
def initDaemonIpfs():
    """
    This function initializes the local IPFS deamon.
    
    Args:
        None.
        
    Return:
        None
        
    Note:
        This functions lauch the local IPFS deamon using a background process
        to not blocking the main process.
    """
    processIPFS = subprocess.Popen(['ipfs', 'daemon'])
    exitCode = processIPFS.wait()
    print(f"IPFS process code: {exitCode}")
    
    
    
####################     HandlerServerTCP class     ####################

class HandlerServerTCP:

    ###static methods ###
   
   
   
    @staticmethod
    def uploadFileToHyperledgerFabric(fileName,cid,timestamp):
        """
        Def:
            Function to upload a file to Hyperledger Fabric Blockchain.
        Args:
            targetFile : full path of the file.
            cid : IPFS CID
            timeStamp : Unix time
        Return:
            upload status
        Note:
            None
        """
        #formatting unix time
        timestamp = datetime.datetime.fromtimestamp(timestamp)
        fmtTimestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        #invoking chaincode
        res = subprocess.run(HyperledgerCmd["AddNewFileIPFS"].format(fileName,cid,fmtTimestamp), capture_output=True, text=True, shell=True)
        cleanRes = res.stderr.strip(' \n\r')
        transactionStatusCode = cleanRes[-3:]
        
        if (transactionStatusCode == "200"):
            print(f"CID '{cid}' successfully stored in Hyperledger Fabric Blockchain")
            return BLOCKCHAIN_OPERATION_COMPLETED
        else:
            print(f"Error invoking the chaincode in Hyperledger Fabric Blockchain: {res}")
            return BLOCKCHAIN_OPERATION_FAILED
        print()
            
            
    @staticmethod
    def isIPFfileStoredInHyperledger(cidToCheck):
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
        
        res = subprocess.run(HyperledgerCmd["GetInfoFileIPFS"].format(cidToCheck), capture_output=True, text=True, shell=True)
        stdout = res.stdout
        
        if stdout != "":
            dictInfoFile = json.loads(stdout)
            #print(f"obtained dict from Hyperledger -> {dictInfoFile}")
            CidReadHyperledger = dictInfoFile["cid"]
            if cidToCheck == CidReadHyperledger:
                ret = True
                
        return ret
        
        
    @staticmethod
    def uploadCIDtoHyperledger(cid,filename):
        """
        Upload file to Hyperledger Fabric.
        
        Args:
            cid : IPFS CID to upload.
            filename : filename
            
        Return:
            Response message to be sent to the client as payload.
        """
        unixTime = time.time()
        operationStatus = ""
        
        #checking if we need to summit modifications to IPFS and blockchain
        isCidStored = HandlerServerTCP.isIPFfileStoredInHyperledger(cid)
        if isCidStored == False:
            #upload IPFS file to Hyperledger Fabric
            print(f"Uploading info from file '{filename}' to Hyperledger Fabric!")
            operationStatus = HandlerServerTCP.uploadFileToHyperledgerFabric(filename,cid,unixTime)
        else:
            print(f"CID '{cid} has been previously stored in Hyperledger'")
            operationStatus = BLOCKCHAIN_OPERATION_FAILED
        
        return operationStatus

    
    
    @staticmethod
    def uploadFileToIPFS(file):
            """
            Def:
                Function to upload a file to IPFS.
            Args:
                file :  filename.
            Return:
                Tuple containing the request status and IPFS CID obtained.
            Note:
                None
            """
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
                raise Exception(f'{response.text}')
                
            return fileIPFSCID
    
    

    @staticmethod
    def copyIPFStoMfs(cid, mfsPath):
        """
        function to copy a IPFS file to the local MFS.
        
        Args:
            cid : cid to be copied.
            mfsPath : path of the folder in MFS.
            
        Return:
            None
        """
        response = requests.post('http://127.0.0.1:5001/api/v0/files/cp', params={
            'arg': [f'/ipfs/{cid}',mfsPath],
            'parents': 'true'})
                                
        if response.status_code == 200:
            print(f"CID {cid} copied to MFS {mfsPath}")
        else:
            print(f"Error {response.status_code} : trying to copy CID {cid} to MFS {mfsPath}")
            raise Exception(f'{response.text}')
        
        
    
    @staticmethod
    def updateIPNS(cid):
        """
        Function to update the pointer of IPNS.
        
        Args :
            cid : cid to be published.
            
        Return:
            None.
        """
        response = requests.post('http://127.0.0.1:5001/api/v0/name/publish', params={'arg': f'/ipfs/{cid}'})
        
        if response.status_code == 200:
            ipnsName = response.json()['Name']
            print(f'URL IPNS: https://ipfs.io/ipns/{ipnsName}')
            return ipnsName
        else:
            print(f'Error trying to publish on IPNS: {response.text}')
            raise Exception(f'{response.text}')
    
    
    
    @staticmethod
    def MFSfolderExistsIPFS(folderPath):
        """
        This function creates the target dir in MFS if the dir 
        doesn't exist.
        
        Args:
            folderPath : target dir.
            
        Return:
            None.
        """
        response = requests.post('http://127.0.0.1:5001/api/v0/files/stat', params={'arg': folderPath})
        
        if response.status_code != 200:
            #the folder doesn't exist so we need to create it
            print(f'Creating folder MFS: {folderPath}')
            response = requests.post('http://127.0.0.1:5001/api/v0/files/mkdir', params={'arg': folderPath, 'parents': 'true'})
            
            if response.status_code != 200:
                print(f"Error while creaing folder {folderPath} in IPFS MFS")
                raise Exception(f'{response.text}')
        


    @staticmethod  
    def getMFSfolderCID(folderPath):
        """
        Function to get the CID of the MFS folder.
        
        Args:
            folderPath : MFS path.
            
        Return:
            The CID of th e MFS folder.
        """
        response = requests.post('http://127.0.0.1:5001/api/v0/files/stat', params={'arg': folderPath})
        
        if response.status_code == 200:
            foldercid = response.json()['Hash']
            print(f'Actual CID of the target folder in MFS {folderPath}: {foldercid}')
            return foldercid
        else:
            print(f"Error {response.status_code} getting folder's CID at MFS")
            raise Exception(f'{response.text}')

    
    
    @staticmethod
    def routineIPFS(filename):
        """
        IPFS routine that will be executed every time that 
        gateway send telemetry to the HTPPS server.
        
        The routine is composed by several steps:
        1 -> check that the mutable folder exists at local MFS.
        2 -> Upload file to IPFS.
        3 -> Copy uploaded file to folder at MFS.
        4 -> Get CID of the folder.
        5 -> publish CID in IPNS
        
        Args:
            filename : filename to upload at local IPFS node.
            
        Return:
            operation status code and new file CID
        """
        retStatus = True
        fileCid = ""
        newfolderCid = ""
        filePathInMFS = DIR_TARGER_FOLDER_MFS + '/' + filename
        
        try:
            HandlerServerTCP.MFSfolderExistsIPFS(DIR_TARGER_FOLDER_MFS)
            fileCid = HandlerServerTCP.uploadFileToIPFS(filename)
            HandlerServerTCP.copyIPFStoMfs(fileCid,filePathInMFS)
            newfolderCid = HandlerServerTCP.getMFSfolderCID(DIR_TARGER_FOLDER_MFS)
            HandlerServerTCP.updateIPNS(newfolderCid)
        except Exception as e:
            print(e)
            retStatus = False
        
        return retStatus, fileCid
    
    
    
    @staticmethod
    def uploadTelemetryBlockchainAndIPFS(cmdParam):
        """
        Function to upload the telemetry received from the client.
        
        Args:
            cmdParam : command parameters
            
        Return:
            Response message to be sent to the client as payload.
        """
        telemetryToBeStored = cmdParam[0]
        print(f"TELEMETRY -> {telemetryToBeStored}")
        operationStatus = BLOCKCHAIN_OPERATION_FAILED
        unixTime = int(time.time())
        fileName = f"telemetry-{unixTime}.txt"
        cid = ""
        statusIpfs = False
        
        #create a temporal file to store telemetry
        with open(fileName, 'w') as file:
            datos = file.write(telemetryToBeStored)
        #upload to IPFS
        statusIpfs, cid = HandlerServerTCP.routineIPFS(fileName)
        #upload to blockchain
        if statusIpfs:
            operationStatus = HandlerServerTCP.uploadCIDtoHyperledger(cid,fileName)
        #delete temporal file
        os.remove(fileName)
        #print("Temperal file {fileName} deleted!")
        return operationStatus
        
        

    ###static defines and variables###
    
    GATEWAY_STORE_CID_EVENT = "STORE_CID"
    GATEWAY_SEND_TELEMTRY_EVENT = "SEND_TELEMETRY"
    
    #getaway event dictionary:  
    #key = command name | 1st value: command pattern , 2nd value : associated function pointer
    gatewayEventDict = {GATEWAY_SEND_TELEMTRY_EVENT : [fr"^{GATEWAY_SEND_TELEMTRY_EVENT}\s+(.*)$",uploadTelemetryBlockchainAndIPFS]}
    
    
    
    ###methods###
    
    
    
    def processRequest(self,payload):
        """
        Process the payload from client.
        
        Args:
            None.
            
        Return:
            None.
        """
        print(f"RECV -> {payload}")
        cmdNameRcv = payload.split()[0]
        #print(f"NAME CMD -> {cmdNameRcv}")
        cmdParamsTuple = tuple()
        response = BLOCKCHAIN_OPERATION_FAILED
        
        for cmdName, value in HandlerServerTCP.gatewayEventDict.items():
            if cmdNameRcv == cmdName:
                #check received msg structure
                pattern = value[0]
                match = re.search(pattern,payload)
                if match:
                    cmdParamsTuple = match.groups()
                    ptrFunction = value[1]
                    response = ptrFunction(cmdParamsTuple)
                    break
                    
        return response



#################### MonitoringForIpfsHyperledger class ####################


class MonitoringForIpfsHyperledger(daemon):

    def __init__(self,pidFile,debugLevel):
        """
        Class constructor
        """
        super().__init__(pidFile,debugLevel) #constructor
        
        self.server = None #TCP server socket 
        self.gateway = None #TCP gateway socket
        #self.gatewayConfig = None
        
        self.handlerObj = HandlerServerTCP()
        

    
    
    def getGatewayConfigFromHyperledgerFabric(self):
        """
        Function to get the gateway configuration from Hyperledger Fabric.
        
        Args:
            None.
        
        Return:
            Dictionary containing the gateway configuration
            
        Note:
            None.
        """
        res = subprocess.run(HyperledgerCmd["GetInfoDevice"].format("Gateway"), capture_output=True, text=True, shell=True)
        stdout = res.stdout
        
        if stdout != "":
            gatewayConfig = json.loads(stdout)
            return gatewayConfig
        else: 
            print("Error getting gateway configuration from Hyperledger Fabric")
            sys.exit(2)
        
        
        
        
    # def initTCPserver(self):
        # """
        # Function that waits until a TCP connection is established with the target gateway.
        
        # Args:
            # None.
            
        # Return:
            # None.
            
        # Note:
            # This function reject all clients except the target gateway device. 
        # """
        # server_address = (LOCALHOST, SERVER_PORT)
        # httpd = http.server.HTTPServer(server_address, HandlerServerTCP)
  
        # context = get_ssl_context("server.cert", "server.key")
        # httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
  
        # print(f"HTTPS server running in {server_address}")
        # httpd.serve_forever()
        
        
    
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
        #gatewayIp =  self.gatewayConfig["ip"]
        
        #print(f"Gateway IP {gatewayIp}")
        
        #creating a TCP socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #setting options
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #binding IP with port
        self.server.bind((LOCALHOST, SERVER_PORT))
        #waiting for connection
        self.server.listen(SERVER_MAX_NUMBER_CONNECTIONS)
    
        #while(not gatewayIsConnected):
        print("Waiting until gateway is connected...")
        #program is blocked here until a connection is established
        clientSocket, clientAddress = self.server.accept()
        clientIp , clientPort = clientAddress
        #checking client
        #if clientIp == gatewayIp:
        gatewayIsConnected = True
        self.gateway = clientSocket
        # else:
            # print("No legitime connection, closing connection...")
            # clientSocket.close()
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
    
    
    
    def serverLoop(self):
        """
        TCP server loop to handler client request
        """
        
        #init TCP server
        print(f"TCP server listening at ({LOCALHOST}:{SERVER_PORT})")
        self.waitUntilGatewayIsConnected()
        
        while True:
            try:
                #wait until some gateway event arrives
                rawData = self.gateway.recv(RX_BUFFER_LEN)
                recvData = rawData.decode()
                
                #verify if gateway connection still open
                isConnectionClosed = self.isSocketClosed()
                
                if isConnectionClosed:#closed
                    self.waitUntilGatewayIsConnected()
                else:#open
                    #processing received data from gateway
                    responsePayload = self.handlerObj.processRequest(recvData)
                    statusCode = ""
                    #sending a response to client
                    if responsePayload == BLOCKCHAIN_OPERATION_COMPLETED:
                        statusCode = OPERATION_COMPLETED_STATUS_CODE
                    else:
                        statusCode = OPERATION_FAILED_STATUS_CODE
                    
                    #sending response
                    self.gateway.sendall(statusCode.encode('utf-8'))
            except ConnectionResetError as e:
                print(f"[EXCEPTION]: {e}")
                #waiting for a new connection in case that an exception
                #occurs
                self.waitUntilGatewayIsConnected()
        
        
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
        
        os.chdir(CERTS_DIR)
        
        #set environment variables before executing any operation in Hyperledger
        for environVarName, environVarValue in HyperledgerEnvVar.items():
            os.environ[environVarName] = environVarValue
        
        #main loop
        self.serverLoop()
        

        
     
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