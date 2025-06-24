/*
    ------ Waspmote Pro Code Example --------

    Explanation: This is the basic Code for Waspmote Pro

    Copyright (C) 2016 Libelium Comunicaciones Distribuidas S.L.
    http://www.libelium.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/*******************************************************************************
 * DS18B20_OneWire_Example
 * -----------------------------------------------------------------------------
 * Example to read temperature from a DS18B20 sensor using the OneWire protocol
 * with Libelium Waspmote.
 *
 * This code assumes you have a DS18B20 sensor connected to the Waspmote's
 * digital pin configured for OneWire (e.g., DIG1).
 *
 * IMPORTANT: Always refer to your specific Waspmote model's documentation
 * to confirm the correct OneWire-compatible pin.
 ******************************************************************************/
// Incluimos la librería de OneWire
#include <WaspOneWire.h>

// Definimos el pin al que está conectado el sensor DS18B20
// (usa un pin digital de Waspmote)
#define ONE_WIRE_BUS DIGITAL6

// Creamos un objeto OneWire
WaspOneWire oneWire(ONE_WIRE_BUS);

// Variable para almacenar la temperatura leída
float temperature = 0.0;

// Array para almacenar la dirección del dispositivo
uint8_t sensorAddress[8];

void setup()
{
  PWR.setSensorPower(SENS_5V, SENS_ON);

  // Encendemos el puerto serie para depuración
  USB.ON();
  USB.println(F("Inicio de lectura de temperatura DS18B20"));

  // Buscamos el primer dispositivo DS18B20 en el bus
  if (oneWire.search(sensorAddress))
  {
    USB.print(F("Sensor encontrado"));
    USB.println();
  }
  else
  {
    USB.println(F("No se encontró ningún sensor en el bus OneWire"));
  }

  oneWire.target_search(0x28);
}

void loop()
{
  // Si encontramos un sensor, leemos su temperatura
  oneWire.reset_search();
  oneWire.target_search(0x28);
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
    int16_t rawTemperature = (data[1] << 8) | data[0];
    temperature = (float)rawTemperature / 16.0;

    // Mostramos la temperatura por USB
    USB.print(F("Temperatura: "));
    USB.print(temperature);
    USB.println(F(" ºC"));
  }
  else
  {
    USB.println(F("No se detectó sensor en esta iteración"));
  }

  // Esperamos 5 segundos antes de la siguiente lectura
  delay(5000);
}

