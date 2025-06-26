/*  
 *  ------ [802_03] - receive XBee packets -------- 
 *  
 *  Explanation: This program shows how to receive packets with 
 *  XBee-802.15.4 modules.
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
#include <WaspWIFI_PRO.h>

#define SERVER_IP "192.168.1.44"
#define SERVER_PORT "5000"
#define SERVER_PROTOCOL "http"
#define SERVER_URL "/"
#define N_MEASURES_TO_SERVER 5

//function definitions
static int sendTelemetryToServer(void);

// define variable
int error;

char body[] = "SEND_TELEMETRY aassaas asasas";

void setup()
{
  // init USB port
  USB.ON();

  // init XBee 
  xbee802.ON();

  //init WI-FI
  WIFI_PRO.ON(SOCKET1);
}


void loop()
{ 
  static int receivedMeasures = 0;
  // receive XBee packet (wait for 10 seconds)
  error = xbee802.receivePacketTimeout(2000);
  
  if( error == 0 ) 
  {
    USB.println(F("New measure received from sensor mote!"));

    // Show data stored in '_payload' buffer indicated by '_length'
    USB.print(F("Data: "));  
    USB.println( xbee802._payload, xbee802._length);
    
    // Show data stored in '_payload' buffer indicated by '_length'
    USB.print(F("Length: "));  
    USB.println( xbee802._length,DEC);

    receivedMeasures = receivedMeasures + 1;

    //send collected measures to HTTP server each N_MEASURES_TO_SERVER measures received
    if (receivedMeasures == N_MEASURES_TO_SERVER)
    {
      receivedMeasures = 0;
      
      //send collected measures to HTTP server
      USB.print(F("Sending pending measures to HTTP server!"));
      sendTelemetryToServer();
    }
  }
}



static int sendTelemetryToServer(void){

  uint8_t error;
  uint8_t status;
  static unsigned long previous;

  // get actual time
  previous = millis();

  // Switch ON 
  error = WIFI_PRO.ON(SOCKET1);

  if (error == 0)
  {    
    USB.println(F("1. WiFi switched ON"));
  }
  else
  {
    USB.println(F("1. WiFi did not initialize correctly"));
  }

  // Set url
  error = WIFI_PRO.setURL( SERVER_PROTOCOL, SERVER_IP, SERVER_PORT, SERVER_URL );

  // check response
  if (error == 0)
  {
    USB.println(F("2. setURL OK"));
  }
  else
  {
    USB.println(F("2. Error calling 'setURL' function"));
    WIFI_PRO.printErrorCode();
  }

  // Join AP 

  // check connectivity
  status =  WIFI_PRO.isConnected();

  // Check if module is connected
  if (status == true)
  {    
    USB.print(F("3. WiFi is connected OK"));

    // 3.1. http request
    error = WIFI_PRO.post(body); 

    // check response
    if (error == 0)
    {
      USB.print(F("3.1. HTTP POST OK. "));
      USB.print(F("HTTP Time from OFF state (ms):"));
      USB.println(millis()-previous);
      
      USB.print(F("\nServer answer:"));
      USB.println(WIFI_PRO._buffer, WIFI_PRO._length);
    }
    else
    {
      USB.println(F("3.1. Error calling 'post' function"));
      WIFI_PRO.printErrorCode();
    }
  }
  else
  {
    USB.print(F("3. WiFi is connected ERROR"));
    USB.print(F(" Time(ms):"));
    USB.println(millis()-previous);
  }


  //////////////////////////////////////////////////
  // 4. Switch OFF
  //////////////////////////////////////////////////  
  WIFI_PRO.OFF(SOCKET1);
  USB.println(F("4. WiFi switched OFF\n\n"));

  return error;
}

