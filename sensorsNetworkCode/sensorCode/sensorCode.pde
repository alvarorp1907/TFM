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

//Defines and macros
#define samplingInterval 20
#define printInterval 800
#define ArrayLenth  40    //times of collection
#define SensorPinPh ANALOG1
#define Offset 0.52           //ph sensor deviation compensate

//functions definition
static double avergearray(int* arr, int number);
static void getPhWithInterval(void);

// Destination MAC address
//////////////////////////////////////////
char RX_ADDRESS[] = "0013A200417EE50B";
//////////////////////////////////////////

// Define the Waspmote ID
char WASPMOTE_ID[] = "node_01";


// define variable
uint8_t error;

//Ph variables
int pHArray[ArrayLenth];   //Store the average value of the sensor feedback
int pHArrayIndex=0;



void setup()
{
  // init USB port
  USB.ON();
  USB.println(F("Sending packets example"));
  
  // store Waspmote identifier in EEPROM memory
  //frame.setID( WASPMOTE_ID );
  
  // init XBee
  //xbee802.ON();

  //enable 5V pin to power sensors
  PWR.setSensorPower(SENS_5V, SENS_ON);
  
}


void loop()
{
  ///////////////////////////////////////////
  // 1. Create ASCII frame
  ///////////////////////////////////////////  

//  // create new frame
//  frame.createFrame(ASCII);  
//  
//  // add frame fields
//  frame.addSensor(SENSOR_STR, "new_sensor_frame");
//  frame.addSensor(SENSOR_BAT, PWR.getBatteryLevel()); 
  

  ///////////////////////////////////////////
  // 2. Send packet
  ///////////////////////////////////////////  

//  // send XBee packet
//  error = xbee802.send( RX_ADDRESS, frame.buffer, frame.length );   
//  
//  // check TX flag
//  if( error == 0 )
//  {
//    USB.println(F("send ok"));
//    
//    // blink green LED
//    Utils.blinkGreenLED();
//    
//  }
//  else 
//  {
//    USB.println(F("send error"));
//    
//    // blink red LED
//    Utils.blinkRedLED();
//  }

  // wait for five seconds
//  delay(5000);

    //getting ph value each 800 ms
    //getPhWithInterval();
}

static double avergearray(int* arr, int number){
  int i;
  int max,min;
  double avg;
  long amount=0;
  if(number<=0){
    USB.println(F("Error number for the array to avraging!/n"));
    return 0;
  }
  if(number<5){   //less than 5, calculated directly statistics
    for(i=0;i<number;i++){
      amount+=arr[i];
    }
    avg = amount/number;
    return avg;
  }else{
    if(arr[0]<arr[1]){
      min = arr[0];max=arr[1];
    }
    else{
      min=arr[1];max=arr[0];
    }
    for(i=2;i<number;i++){
      if(arr[i]<min){
        amount+=min;        //arr<min
        min=arr[i];
      }else {
        if(arr[i]>max){
          amount+=max;    //arr>max
          max=arr[i];
        }else{
          amount+=arr[i]; //min<=arr<=max
        }
      }//if
    }//for
    avg = (double)amount/(number-2);
  }//if
  return avg;
}

void initPhMeter(){
  
}

static void getPhWithInterval(void){
  static unsigned long samplingTime = millis();
  static unsigned long printTime = millis();
  static float pHValue,voltage;
  if(millis()-samplingTime > samplingInterval)
  {
      pHArray[pHArrayIndex++]=analogRead(SensorPinPh);
      if(pHArrayIndex==ArrayLenth)pHArrayIndex=0;
      voltage = avergearray(pHArray, ArrayLenth)*3.3/1023;
      pHValue = 3.5*voltage+Offset;
      samplingTime= millis();
  }
  if(millis() - printTime > printInterval)   //Every 800 milliseconds, print a numerical, convert the state of the LED indicator
  {
    USB.print(F("Voltage:"));
    USB.print(voltage);
    USB.print(F("ADC value :"));
    USB.print(analogRead(SensorPinPh));
    USB.print(F("    pH value: "));
    USB.println(pHValue);
    printTime=millis();
  }
}

