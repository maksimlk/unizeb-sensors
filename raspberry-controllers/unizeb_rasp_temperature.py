# Simple python script to control the Raspberry PI, receive data from the serial port, add timestamp/sensors names
# and upload it to the database.
# !Version 0.02

# TODO - LIST:
# TODO IF THE CONNECTION WAS NOT SUCCESSFUL -  WRITE TO THE LOCAL FILE.
# TODO CHECK IF THE ARDUINO WAS CONNECTED -  BOOLEAN VARIABLE (+ LOGS TO CONSOLE)
# TODO MORE CHECKS FOR THE ERRORS & CHECK THE INPUT FROM THE ARDUINO.
# TODO AUTOMATIC FILE LOGGING & FILE DELETING AFTER CERTAIN AMOUNT OF DATES.

import serial
import time
from datetime import datetime
import mysql.connector
from mysql.connector import errorcode

# !!! CONFIG PART !!!

log_file = open("temperature_log", "a")

config = {
    'user': 'unizeb-temperature-sensor',
    'password': 'password',
    'host': '192.168.186.5',
    'database': 'measurements',
    'raise_on_warnings': True
}

START_MARKER = '$'
END_MARKER = '!'

# USE COM*NUMBER* FOR WINDOWS AND /dev/ttyUSB*NUMBER* FOR UNIX-BASED SYSTEMS
ARDUINO1_ADDRESS = '/dev/ttyUSB0'
ARDUINO2_ADDRESS = '/dev/ttyUSB1'
ARDUINO3_ADDRESS = '/dev/ttyUSB2'
ARDUINO4_ADDRESS = '/dev/ttyUSB3'

BAUD_RATE = 9600

# !!! END OF CONFIG PART !!!

ARDUINO1_COM = serial.Serial(ARDUINO1_ADDRESS, BAUD_RATE, timeout=.1)
print("** USB0 connected **")
ARDUINO2_COM = serial.Serial(ARDUINO2_ADDRESS, BAUD_RATE, timeout=.1)
print("** USB1 connected **")
ARDUINO3_COM = serial.Serial(ARDUINO3_ADDRESS, BAUD_RATE, timeout=.1)
print("** USB2 connected **")
# ADRDUINO4_COM = serial.Serial(ARDUNO4_ADDRESS, BAUD_RATE, timeout=.1)

try:
    database_con = mysql.connector.connect(**config)
    print("Connection to the database successful")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)


cursor = database_con.cursor()


# MySQL queue to upload the measurements results.
add_measurement_sql = ("INSERT INTO temperature_measurements "
                       "(time_date, section_name, sensor_name, temperature) "
                       "VALUES (%s, %s, %s, %s)")

# Parsing of the data, slicing the strings, joining them into the same data structure TODO!!!
def parse_data(data):
    temp_data = data.splitlines()
    data_struct = list()
    for i in range(0, temp_data.len()-3):
        data_struct.append((
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            temp_data[1],
            temp_data[i+2].split()[0],
            temp_data[i+2].split()[1],
        ))
    print(data_struct)
    return data_struct


# Sending data to the MySQL database
def send_data(data_struct):
    for data in data_struct:
        cursor.execute(add_measurement_sql, data)
    database_con.commit()


# Method to read data from the USB input
def receive_data(com):
    data_stream = ""
    byte_count = -1
    x = bytes("test", encoding="utf-8")
    while x.decode("utf-8") != START_MARKER:
        x = com.read()
    while x.decode("utf-8") != END_MARKER:
        x = com.read()
        data_stream += x.decode("utf-8")
        byte_count += 1
    data_stream += x.decode("utf-8")
    print(data_stream)
    return data_stream


# Infinite loop waiting for the incoming signals.
while True:
    if ARDUINO1_COM.inWaiting() > 0:
        data_01 = receive_data(ARDUINO1_COM)
        send_data(parse_data(data_01))
    if ARDUINO2_COM.inWaiting() > 0:
        data_02 = receive_data(ARDUINO2_COM)
        send_data(parse_data(data_02))
    if ARDUINO3_COM.inWaiting() > 0:
        data_03 = receive_data(ARDUINO3_COM)
        send_data(parse_data(data_03))
    # if ARDUINO4_COM.inWaiting() > 0:
    #    data_04 = receive_data(ARDUINO4_COM)
    #    send_data(parse_data(data_04))
