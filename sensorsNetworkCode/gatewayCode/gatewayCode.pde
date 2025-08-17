#include <WaspXBee802.h>
#include <WaspWIFI_PRO.h>
#include <WaspAES.h>

//defines 

//HW
#define HW_WIFI_SOCKET SOCKET1

//sleep mode
#define DELAY "03"

//server
#define SERVER_IP "192.168.1.44"
#define SERVER_PORT "5000"
#define TCP_LOCAL_PORT "12345"
#define TCP_REMOTE_PORT "5000"
#define SEND_TELEMETRY_CMD "SEND_TELEMETRY"

//rx buffer
#define N_MEASURES_TO_SERVER 2
#define N_BYTES_PER_RX_FRAME 66 + 4 //adding 4 extra byte to avoid overflow<WaspAES.h>
#define LEN_RX_BUFFER N_MEASURES_TO_SERVER*N_BYTES_PER_RX_FRAME

//frame fields
#define N_NAME_FIELD 2
#define N_SEQUENCE_FIELD 3
#define N_TEMPERATURE_FIELD 4
#define N_PH_FIELD 5
#define N_TURBIDITY_FIELD 6

//NTP
#define TIME_ZONE 2 //GMT+2 (daylight season)
#define NTP_SERVER_1 "time.nist.gov"
#define NTP_INDEX_SERVER_1 1
#define NTP_SERVER_2 "wwv.nist.gov"
#define NTP_INDEX_SERVER_2 2

//AES128
#define KEY_AES128 "Ak976GbNgqyp16bj"
#define KEY_AES128_SERVER "d09bfpJkrbhr638v"
//types
typedef struct{
  char * waterTemperature;
  char * ph;
  char * turbidity;
  char * name;
  char * seq;
}dataField_t;

//function definitions
static uint8_t sendTelemetryToServer(void);
static dataField_t getDataFields(char * frame);
static uint8_t synchronizeRTC(void);
static void goToSleepMode(void);

//local variables
static int error;
static char rxBuffer [LEN_RX_BUFFER];
static bool isRtcSync = false;

void setup()
{
  // init USB port
  USB.ON();

  // init XBee 
  xbee802.ON();

  //init WI-FI
  //WIFI_PRO.ON(HW_WIFI_SOCKET);

  //configuration of time synchronitation of RTC
  //through WIFI
  InitsynchronitationTime();

  //initializing rx buffer
  memset(rxBuffer,0,sizeof(rxBuffer));
}

void loop()
{ 
  static int receivedMeasures = 0;
  static int posBuf = 0;
  char tempBuf [90];
  dataField_t dataFields = {0};
  uint8_t posTempBuf = 0;
  char decrypted_message[128];
  uint16_t sizeDecrypted; 
  //uint8_t encrypted_message[80];//5 blocks
  uint16_t encrypted_length;
  
  // receive XBee packet
  error = xbee802.receivePacketTimeout(5000);
  
  if( error == 0 ) 
  {
    USB.println(F("New measure received from sensor mote!"));

    // Show data stored in '_payload' buffer indicated by '_length'
    USB.print(F("Received data from IEE802.15.4: "));  
    USB.println( xbee802._payload, xbee802._length);
    
    // Show data stored in '_payload' buffer indicated by '_length'
    USB.print(F("Length: "));  
    USB.println( xbee802._length,DEC);

    //Decrypting received message with AES128
    //memset(encrypted_message,0,sizeof(encrypted_message));
    //memcpy(encrypted_message,xbee802._payload,xbee802._length);
    encrypted_length = AES.sizeOfBlocks((char *) xbee802._payload);

    AES.decrypt(128,KEY_AES128,xbee802._payload,encrypted_length, (uint8_t *) decrypted_message, &sizeDecrypted, ECB, ZEROS);    
    //USB.print(F("decrypted message:"));
    //USB.print((char *) decrypted_message);
       
    //processing received frame
    dataFields = getDataFields(decrypted_message);
    memset(tempBuf,0,sizeof(tempBuf));
    
    if (receivedMeasures == 0){
      sprintf(tempBuf,"%s NAME:%s SEQ:%s %s C %s %s %% ",SEND_TELEMETRY_CMD,dataFields.name,dataFields.seq,dataFields.waterTemperature,dataFields.ph,dataFields.turbidity);
    }else{
      sprintf(tempBuf,"NAME:%s SEQ:%s C %s %s %s %% ",dataFields.name,dataFields.seq,dataFields.waterTemperature,dataFields.ph,dataFields.turbidity);
    }
    
    posTempBuf = strlen(tempBuf);
    
    if (isRtcSync)
    {
      sprintf(&tempBuf[posTempBuf],"TIME:%s \n\r",RTC.getTime());
    }else{
      sprintf(&tempBuf[posTempBuf],"TIME: not sync yet \n\r");
    }

    USB.println(sizeof(tempBuf));
    
    //stroring in buffer
    memcpy(&rxBuffer[posBuf], tempBuf, strlen(tempBuf));
    posBuf = posBuf + strlen(tempBuf);
    USB.println(rxBuffer);
    
    // incrementing counter of collected measures
    receivedMeasures = receivedMeasures + 1;
    USB.println(receivedMeasures);
   
     //send collected measures to TCP server each N_MEASURES_TO_SERVER measures received
    if (receivedMeasures == N_MEASURES_TO_SERVER)
    {
     receivedMeasures = 0;
      
     //send collected measures to TCP server
     USB.println(F("Sending pending measures to TCP server!"));
     USB.print(rxBuffer);
     sendTelemetryToServer();

     //erasing buffer
     memset(rxBuffer,0,sizeof(rxBuffer));
     posBuf = 0;
      
    }
  }
}



static uint8_t sendTelemetryToServer(){

  uint8_t error = 0;
  uint8_t status = 0;
  unsigned long previous = 0;
  uint16_t socket_handle = 0;
  uint8_t encrypted_message[192];
  
  //////////////////////////////////////////////////
  // 1. Switch ON
  //////////////////////////////////////////////////  
  error = WIFI_PRO.ON(HW_WIFI_SOCKET);

  if( error == 0 )
  {    
    USB.println(F("1. WiFi switched ON"));
  }
  else
  {
    USB.println(F("1. WiFi did not initialize correctly"));
  }


  //////////////////////////////////////////////////
  // 2. Check if connected
  //////////////////////////////////////////////////  

  // get actual time
  previous = millis();

  // check connectivity
  status =  WIFI_PRO.isConnected();

  // check if module is connected
  if( status == true )
  {    
    USB.print(F("2. WiFi is connected OK"));
    USB.print(F(" Time(ms):"));    
    USB.println(millis()-previous);

    // get IP address
    error = WIFI_PRO.getIP();

    if (error == 0)
    {    
      USB.print(F("IP address: "));    
      USB.println( WIFI_PRO._ip );     
    }
    else
    {
      USB.println(F("getIP error"));     
    }
  }
  else
  {
    USB.print(F("2. WiFi is connected ERROR")); 
    USB.print(F(" Time(ms):"));    
    USB.println(millis()-previous); 
  }



  //////////////////////////////////////////////////
  // 3. TCP
  //////////////////////////////////////////////////  

  // Check if module is connected
  if (status == true)
  {   
    
    //////////////////////////////////////////////// 
    // 3.1. Open TCP socket
    ////////////////////////////////////////////////
    error = WIFI_PRO.setTCPclient( SERVER_IP, TCP_REMOTE_PORT, TCP_LOCAL_PORT);

    // check response
    if (error == 0)
    {
      // get socket handle (from 0 to 9)
      socket_handle = WIFI_PRO._socket_handle;
      
      USB.print(F("3.1. Open TCP socket OK in handle: "));
      USB.println(socket_handle, DEC);
    }
    else
    {
      USB.println(F("3.1. Error calling 'setTCPclient' function"));
      WIFI_PRO.printErrorCode();
      status = false;   
    }

    if (status == true)
    {   
      
      //encrypts frame at application layer with AES128
      AES.encrypt(128,KEY_AES128_SERVER,rxBuffer,encrypted_message, ECB, ZEROS);
      USB.print("Encrypted data to be sent to TCP server:");
      USB.print((char *) encrypted_message);

      //encode the data in HEX
      char hex_string[192];  // espacio para hex + terminador
      memset(hex_string,0,sizeof(hex_string));
      for (int i = 0; i < 192; i++) {
        sprintf(&hex_string[i*2], "%02X", encrypted_message[i]);
      }

      
      ////////////////////////////////////////////////
      // 3.2. send data
      ////////////////////////////////////////////////
      error = WIFI_PRO.send( socket_handle,hex_string);

      // check response
      if (error == 0)
      {
        USB.println(F("3.2. Send data OK"));   
      }
      else
      {
        USB.println(F("3.2. Error calling 'send' function"));
        WIFI_PRO.printErrorCode();       
      }

      ////////////////////////////////////////////////
      // 3.3. Wait for answer from server
      ////////////////////////////////////////////////
      USB.println(F("Listen to TCP socket:"));
      error = WIFI_PRO.receive(socket_handle, 30000);

      // check answer  
      if (error == 0)
      {
        USB.println(F("\n========================================"));
        USB.print(F("Data: "));  
        USB.println( WIFI_PRO._buffer, WIFI_PRO._length);

        USB.print(F("Length: "));  
        USB.println( WIFI_PRO._length,DEC);
        USB.println(F("========================================"));
      }else{
        USB.println(F("Timeout while waiting a response from TCP server"));
      }

      ////////////////////////////////////////////////
      // 3.4. Time synchronitation using NTP protocol
      ////////////////////////////////////////////////
      if (status == true)
      {   
        status = synchronizeRTC();
      }
      ////////////////////////////////////////////////
      // 3.5. close socket
      ////////////////////////////////////////////////
      error = WIFI_PRO.closeSocket(socket_handle);

      // check response
      if (error == 0)
      {
        USB.println(F("3.3. Close socket OK"));   
      }
      else
      {
        USB.println(F("3.3. Error calling 'closeSocket' function"));
        WIFI_PRO.printErrorCode(); 
      }
    }

    return error;
}


  //////////////////////////////////////////////////
  // 4. Switch OFF
  //////////////////////////////////////////////////  
  WIFI_PRO.OFF(HW_WIFI_SOCKET);
  USB.println(F("4. WiFi switched OFF\n\n"));

  return error;
}

static dataField_t getDataFields(char * frame){
  
  char * token;
  int nField = 0;
  dataField_t dataFields = {0};
  
  token = strtok( frame, "#");

  while (token != NULL) {
    
    if (nField == N_NAME_FIELD){
      dataFields.name = token;
    }else if (nField == N_SEQUENCE_FIELD){
      dataFields.seq = token;
    }else if (nField == N_TEMPERATURE_FIELD){
      dataFields.waterTemperature = token;
    }else if (nField == N_PH_FIELD){
      dataFields.ph = token;
    }else if (nField == N_TURBIDITY_FIELD){
      dataFields.turbidity = token;
    }
    
    token = strtok(NULL, "#");
    nField++;
  }

  return dataFields;
}

static void InitsynchronitationTime(){

  uint8_t error=0;
  uint8_t status=0;
  unsigned long previous=0;

  /////////////////////////////////////////////////
  // 1. Switch ON
  //////////////////////////////////////////////////  
  error = WIFI_PRO.ON(HW_WIFI_SOCKET);

  if (error == 0)
  {    
    USB.println(F("1. WiFi switched ON"));
  }
  else
  {
    USB.println(F("1. WiFi did not initialize correctly"));
  }


  //////////////////////////////////////////////////
  // 2. Check if connected
  //////////////////////////////////////////////////  

  // get actual time
  previous = millis();

  // check connectivity
  status =  WIFI_PRO.isConnected();

  // Check if module is connected
  if (status == true)
  {    
    USB.print(F("2. WiFi is connected OK"));
//    USB.print(F(" Time(ms):"));    
//    USB.println(millis()-previous);
  }
  else
  {
    USB.print(F("2. WiFi is connected ERROR")); 
//    USB.print(F(" Time(ms):"));    
//    USB.println(millis()-previous); 
  }



  //////////////////////////////////////////////////
  // 3. NTP server
  //////////////////////////////////////////////////  

  // Check if module is connected
  if (status == true)
  {   

    // 3.1. Set NTP Server (option1)
    error = WIFI_PRO.setTimeServer(NTP_INDEX_SERVER_1, NTP_SERVER_1);

    // check response
    if (error == 0)
    {
      USB.println(F("3.1. Time Server1 set OK"));   
    }
    else
    {
      USB.println(F("3.1. Error calling 'setTimeServer' function"));
      WIFI_PRO.printErrorCode();
      status = false;   
    }
    
    
    // 3.2. Set NTP Server (option2)
    error = WIFI_PRO.setTimeServer(NTP_INDEX_SERVER_2, NTP_SERVER_2);

    // check response
    if (error == 0)
    {
      USB.println(F("3.2. Time Server2 set OK"));   
    }
    else
    {
      USB.println(F("3.2. Error calling 'setTimeServer' function"));
      WIFI_PRO.printErrorCode();
      status = false;   
    }

    // 3.3. Enabled/Disable Time Sync
    //when the flag is true the time will be refreshed each
    //to hours
//    if (status == true)
//    { 
//      error = WIFI_PRO.timeActivationFlag(true);
//
//      // check response
//      if( error == 0 )
//      {
//        USB.println(F("3.3. Network Time-of-Day Activation Flag set OK"));   
//      }
//      else
//      {
//        USB.println(F("3.3. Error calling 'timeActivationFlag' function"));
//        WIFI_PRO.printErrorCode();  
//        status = false;        
//      } 
//    }

    // 3.4. set GMT
    if (status == true)
    {     
      error = WIFI_PRO.setGMT(TIME_ZONE);

      // check response
      if (error == 0)
      {
        USB.print(F("3.4. GMT set OK to "));   
        USB.println(TIME_ZONE, DEC);
      }
      else
      {
        USB.println(F("3.4. Error calling 'setGMT' function"));
        WIFI_PRO.printErrorCode();       
      } 
    }
  }

  //synchronize time in RTC
  // Check if module is connected
  if (status == true)
  {
    WIFI_PRO.timeActivationFlag(true);   
    status = synchronizeRTC();
  }

  //////////////////////////////////////////////////
  // 4. Switch OFF
  //////////////////////////////////////////////////  
  USB.println(F("4. WiFi switched OFF\n")); 
  WIFI_PRO.OFF(HW_WIFI_SOCKET);

  delay(5000);
  
  // Init RTC
  RTC.ON();
  USB.print(F("Current RTC settings:"));
  USB.println(RTC.getTime());
  
}

static uint8_t synchronizeRTC(void){
  uint8_t status = true;

  //set RTC
  error = WIFI_PRO.setTimeFromWIFI();
  
  // check response
  if (error == 0)
  {
    USB.print(F("3. Set RTC time OK. Time:"));
    USB.println(RTC.getTime());
    isRtcSync = true;
  }
  else
  {
    USB.println(F("3. Error calling 'setTimeFromWIFI' function"));
    WIFI_PRO.printErrorCode();
    status = false;
  }

  return status;
}

static void goToSleepMode(void){
  
  // Setting alarm 1 in offset mode:
  // Alarm 1 is set 15 seconds later
  
  char buf [15];
  
  sprintf(buf,"00:00:00:%s",DELAY);
  RTC.setAlarm1(buf,RTC_OFFSET,RTC_ALM1_MODE2);

//  USB.print(F("Time [Day of week, YY/MM/DD, hh:mm:ss]: "));
//  USB.println(RTC.getTime());
//
//  USB.println(F("Alarm1 is set to OFFSET mode: "));
//  USB.println(RTC.getAlarm1());

  // Setting Waspmote to Low-Power Consumption Mode
  //USB.println(F("entering into sleep mode"));
  PWR.sleep(SENS_OFF | SD_OFF | XBEE_ON);
  
  // After setting Waspmote to power-down, UART is closed, so it
  // is necessary to open it again
  USB.ON();
  RTC.ON();
  xbee802.ON();

  //USB.println(F("Waspmote wake up!"));
  //USB.print(F("Time: "));
  //USB.println(RTC.getTime());

  if( intFlag & RTC_INT )
  {
    intFlag &= ~(RTC_INT); // Clear flag
  }
}

