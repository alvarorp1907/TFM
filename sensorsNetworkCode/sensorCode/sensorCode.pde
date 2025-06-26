/*  
 *  ------ [802_02] - send packets -------- 
 *  
 *  Explanation: This program shows how to send packets to a gateway
 *  indicating the MAC address of the receiving XBee module 
 *  
 *  Copyright (C) 2016 Libelium Comunicaciones Distribuidas S.L. 
 *  http://www.libelium.com 
 *  
 *  This program is free software: you can redistribute it and/or modify 
 *  it under the terms of the GNU General Public License as published by 
 *  the Free Software Foundation, either version 3 of the License, or 
 *  (at your option) any later version. 
 *  
 *  This program is distributed in the hope that it will be useful, 
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of 
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
 *  GNU General Public License for more details. 
 *  
 *  You should have received a copy of the GNU General Public License 
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>. 
 *  
 *  Version:           3.0
 *  Design:            David Gascón 
 *  Implementation:    Yuri Carmona
 */
 
#include <WaspXBee802.h>
#include <WaspFrame.h>
#include <WaspOneWire.h>
#include <math.h>

//Defines and macros
#define PH_BUFFER_LEN  10
#define SENSOR_PIN_PH ANALOG1
#define OFFSET_PH_SENSOR 0.52
#define ONE_WIRE_BUS DIGITAL6
#define ADC_VREF 3.3
#define SENSOR_TEMPERATURE_ID 70
#define SENSOR_PH_ID 71
#define SENSOR_TURBIDITY_ID 72


//functions definition
static float getPh(void);
static float getTemperature(void);
static int getTurbidity(void);
static void sendMeasuresToGateway(float temperature, float ph, int turbidity);

// Destination MAC address
static char RX_ADDRESS[] = "0013A200417EE50B";
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
  frame.setID("SENSOR_WASPMOTE");
  
  // init XBee
  xbee802.ON();
  
}


void loop()
{
  static float temperature, ph;
  static int turbidity;
  
  //getting Ph, temperature and turbidity from connected sensors
  USB.println("");
  USB.println(F("--- Quality of water ---"));
  turbidity = getTurbidity();
  temperature = getTemperature();
  ph = getPh();
  USB.println(F("------------------------"));

  //sending collected data to the gateway through xbee module
  sendMeasuresToGateway(temperature,ph,turbidity);

  //desabling 5V pin to save battery
  PWR.setSensorPower(SENS_5V, SENS_OFF);
  //wait for five seconds
  delay(10000);
  //enabling battery and wait of 1s to ensure 
  //a stable power signal
  PWR.setSensorPower(SENS_5V, SENS_ON);
  delay(1000);
  
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

  USB.print(F("pH value: "));
  USB.println(ph);
  
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
    USB.print(F("Temperature: "));
    USB.print(temperature);
    USB.println(F(" C"));
  }
  else
  {
    USB.println(F("No temperature sensor detected!!"));
  }

  return temperature;
}

static int getTurbidity(void){
  //ToDo: to complete
  USB.print(F("Turbidity mock measure: "));
  USB.println("20%");
  
  return 20;
}

static void sendMeasuresToGateway(float temperature, float ph, int turbidity){
  
  // create new ASCII frame
  frame.createFrame(ASCII);  
  
  // add frame fields
  frame.addSensor(SENSOR_WATER_WT, temperature);
  frame.addSensor(SENSOR_WATER_PH, ph); 
  frame.addSensor(SENSOR_WATER_TURB, turbidity);

  // send XBee packet
  error = xbee802.send( RX_ADDRESS, frame.buffer, frame.length );   
  
  // check TX flag
  if( error == 0 )
  {
    USB.println(F("send ok"));
    
    // blink green LED
    Utils.blinkGreenLED();
    
  }
  else 
  {
    USB.println(F("send error"));
    
    // blink red LED
    Utils.blinkRedLED();
  }
}

