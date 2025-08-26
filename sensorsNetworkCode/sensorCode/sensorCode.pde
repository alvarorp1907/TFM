/*  
 *  Sensor code
 */
 
#include <WaspXBee802.h>
#include <WaspAES.h>
#include <WaspOneWire.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>

//Defines and macros

//debug mode
#define DEBUG_MODE

//Sensors
#define PH_BUFFER_LEN  10
#define SENSOR_PIN_PH ANALOG1
#define OFFSET_PH_SENSOR 0.52
#define ONE_WIRE_BUS DIGITAL6
#define ADC_VREF 3.3
#define SENSOR_TEMPERATURE_ID 70
#define SENSOR_PH_ID 71
#define SENSOR_TURBIDITY_ID 72
#ifdef DEBUG_MODE
#define DELAY "40" //s
#else
#define DELAY "60" //1h
#endif

//AES128 encryption
#define KEY_AES128 "Ak976GbNgqyp16bj"

//functions definition
static float getPh(void);
static float getTemperature(void);
static int getTurbidity(void);
static void sendMeasuresToGateway(float temperature, float ph, int turbidity);
static void goToSleepMode(void);

// Destination MAC address
static char RX_ADDRESS[] = "0013A200412A16C3";
// Define the Waspmote ID
static char WASPMOTE_ID[] = "node_01";
// define variable
static uint8_t error;

//Note: is important the connect the battery
//in order to provide enough current to the sensors and RF modules
//if you dont connect the external battery, the microcontroller
//would reboot periodically

void setup()
{
  //init 5V pin
  PWR.setSensorPower(SENS_5V, SENS_ON);
  // init USB port
  USB.ON();
  
  // store Waspmote identifier in EEPROM memory
  //frame.setID("SENSOR_WASPMOTE");
  
  // init XBee
  xbee802.ON();
  
}


void loop()
{
  static float temperature, ph;
  static int turbidity;

  #ifdef DEBUG_MODE
    unsigned long startTime;
    unsigned long elapsedTime;

    startTime = millis();
    USB.println();
    USB.println(F("**** Entering in working mode ***"));
  #endif
  
  //getting Ph, temperature and turbidity from connected sensors
  
  #ifdef DEBUG_MODE
    USB.println("");
    USB.println(F("--- Quality of water ---"));
  #endif
  
  turbidity = getTurbidity();
  temperature = getTemperature();
  ph = getPh();
  
  #ifdef DEBUG_MODE
    USB.println(F("------------------------"));
  #endif

  //sending collected data to the gateway through xbee module
  sendMeasuresToGateway(temperature,ph,turbidity);

  #ifdef DEBUG_MODE
    elapsedTime = millis() - startTime; //elapsed time while adquiring measures from sensors
    USB.println(F("Elapsed time while adquiring measures from sensors:"));
    USB.print(elapsedTime,DEC);
    USB.println(F(" ms"));
    USB.println();
    USB.println(F("*********************************"));
    USB.println();
  #endif

  //entering into sleep mode
  goToSleepMode();
  
}

static float getPh(void){

  int buf[PH_BUFFER_LEN];
  int temp = 0;
  int sum = 0;
  float voltage = 0;
  float ph = 0;
  
  //Get 10 sample value from the sensor for smooth the value
  for(int i=0;i<10;i++)
  { 
    buf[i]=analogRead(SENSOR_PIN_PH);
    delay(10);
  }
  
  //sort the analog from small to large
  for(int i=0;i<9;i++)
  {
    for(int j=i+1;j<10;j++)
    {
      if(buf[i]>buf[j])
      {
        temp=buf[i];
        buf[i]=buf[j];
        buf[j]=temp;
      }
    }
  }

  //take the average value of 6 center sample
  for(int i=2;i<8;i++){
   sum+=buf[i]; 
  }

  //calculate Ph value
  voltage =(float)sum*ADC_VREF/1023/6;
  ph = 3.5*voltage + OFFSET_PH_SENSOR;
  #ifdef DEBUG_MODE
    USB.print(F("pH value: "));
    USB.println(ph);
  #endif
  
  return ph;
}

static float getTemperature(void){
  
  static WaspOneWire oneWire(ONE_WIRE_BUS);
  uint8_t sensorAddress[8];
  int16_t rawTemperature;
  float temperature=-200;
  
  // Si encontramos un sensor, leemos su temperatura
  oneWire.reset_search();
  //oneWire.target_search(0x28);
  if (oneWire.search(sensorAddress))
  {
    // Solicitamos la conversión de temperatura
    oneWire.reset();
    oneWire.select(sensorAddress);
    oneWire.write(0x44);  // Comando para iniciar conversión de temperatura

    // Esperamos el tiempo necesario para la conversión (750 ms para 12 bits)
    delay(800);

    // Leemos los datos del scratchpad
    oneWire.reset();
    oneWire.select(sensorAddress);
    oneWire.write(0xBE);  // Comando para leer el scratchpad

    // Leemos los dos primeros bytes del scratchpad (LSB y MSB)
    uint8_t data[9];
    for (int i = 0; i < 9; i++)
    {
      data[i] = oneWire.read();
    }

    // Calculamos la temperatura a partir de los datos leídos
    rawTemperature = (data[1] << 8) | data[0];
    temperature = (float)rawTemperature / 16.0;

    // Mostramos la temperatura por USB
    #ifdef DEBUG_MODE
      USB.print(F("Temperature: "));
      USB.print(temperature);
      USB.println(F(" C"));
    #endif
  }
  else
  {
    USB.println(F("No temperature sensor detected!!"));
  }

  return temperature;
}

static int getTurbidity(void){
  //ToDo: to complete

  #ifdef DEBUG_MODE
    USB.print(F("Turbidity mock measure: "));
    USB.println("20%");
  #endif
  
  return 20;
}

static void sendMeasuresToGateway(float temperature, float ph, int turbidity){

  char txBuffer[80]="";
  uint8_t encrypted_message[80]; //5 blocks of 16 bytes
  uint8_t xbeeBuffer [82]; //2 bytes to store the length of the encrypted data + 80 to store the encrypted data
  char tempAux[10] = "";
  char phAux[10] = "";
  uint16_t bytes;

  //initialize buffer
  memset(encrypted_message,0,sizeof(encrypted_message));
  
  //fill tx buffer with the collected data
  dtostrf(temperature,0, 2, tempAux);// parameter width is o to avoid extra spaces
  dtostrf(ph,0,2, phAux);// parameter width is o to avoid extra spaces
  sprintf(txBuffer,"#Temp:%s#pH:%s#turb:%d#",tempAux,phAux,turbidity);

  //calculating length of plain text for AES128 encryption
  bytes = AES.sizeOfBlocks(txBuffer);

  //encrypts frame at application layer with AES128
  AES.encrypt(128,KEY_AES128,txBuffer,encrypted_message, ECB, ZEROS);

  //in debug mode we check the encrypted msg
  #ifdef DEBUG_MODE
    uint8_t decrypted_msg[80]="";
    uint16_t sizeDecrypted;

    //decrypting message to check encryption
    AES.decrypt(128,KEY_AES128,encrypted_message,bytes,decrypted_msg, &sizeDecrypted, ECB, ZEROS);
    decrypted_msg[sizeDecrypted] = '\0';

    //printing relevant information
    USB.println();
    USB.println(F("---- Encyption info ----"));
    USB.println(F("Plain data"));
    USB.println(txBuffer);
    USB.println(F("Encrypted data"));
    USB.println((char *)encrypted_message);
    USB.println(F("Length encrypted:"));
    USB.println(bytes,DEC);
    USB.println(F("Decrypted message:"));
    USB.println((char *)decrypted_msg);
    USB.println(F("Size decrypted:"));
    USB.println(sizeDecrypted,DEC);
    USB.println(F("-----------------------"));
    USB.println();
  #endif
  

  //fill xbee buffer to be transmitted
  //                        2Bytes        80Bytes max
  //XbeeBuffer fields = |encryptedLength|EncryptedData|
  xbeeBuffer[0] = (bytes & 0xFF00) >> 8;
  xbeeBuffer[1] = (bytes & 0x00FF);
  memcpy(&xbeeBuffer[2],encrypted_message,sizeof(encrypted_message));
  
  // send XBee packet
  error = xbee802.send( RX_ADDRESS, xbeeBuffer, sizeof(xbeeBuffer) );

  #ifdef DEBUG_MODE
    USB.println(F("--- xbee TX status ---"));
  #endif
  
  // check TX flag
  if( error == 0 )
  {
    #ifdef DEBUG_MODE
      USB.println(F("send ok"));
    #endif
    
    // blink green LED
    Utils.blinkGreenLED();
    
  }
  else 
  {
    #ifdef DEBUG_MODE
      USB.print(F("send error:"));
      USB.println(error,DEC);
    #endif
    
    // blink red LED
    Utils.blinkRedLED();
  }
  
  #ifdef DEBUG_MODE
    USB.println(F("-----------------------"));
    USB.println();
  #endif
}

static void goToSleepMode(void){
  
  // Setting alarm 1 in offset mode:
  // Alarm 1 is set 15 seconds later
  
  char buf [15];

  #ifdef DEBUG_MODE
    sprintf(buf,"00:00:00:%s",DELAY);
  #else
    sprintf(buf,"00:00:%s:00",DELAY);
  #endif
  RTC.setAlarm1(buf,RTC_OFFSET,RTC_ALM1_MODE2);

//  USB.print(F("Time [Day of week, YY/MM/DD, hh:mm:ss]: "));
//  USB.println(RTC.getTime());
//
//  USB.println(F("Alarm1 is set to OFFSET mode: "));
//  USB.println(RTC.getAlarm1());

  //Power off modules 
  PWR.setSensorPower(SENS_5V, SENS_OFF);

  // Setting Waspmote to Low-Power Consumption Mode
  #ifdef DEBUG_MODE
    USB.println(F("**** Entering in sleep mode ***"));
  #endif
  
  PWR.sleep(ALL_OFF);
  
  // After setting Waspmote to power-down, UART is closed, so it
  // is necessary to open it again
  USB.ON();
  
  #ifdef DEBUG_MODE
    USB.println();
    USB.println(F("Waspmote wake up!"));
    USB.println();
    USB.println(F("*******************************"));
  #endif
  
  RTC.ON();
  //USB.print(F("Time: "));
  //USB.println(RTC.getTime());

  //power on modules
  PWR.setSensorPower(SENS_5V, SENS_ON);
  delay(1000);

  // init XBee
  xbee802.ON();
  
  // Waspmote wakes up at '11:25:30'
  if( intFlag & RTC_INT )
  {
    intFlag &= ~(RTC_INT); // Clear flag
  }
}

