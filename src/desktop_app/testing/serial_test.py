import serial
import time

PORT = "COM3"   # or /dev/ttyUSB0, /dev/tty.usbmodemXXXX
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # let board reset

# Read startup message
print(ser.readline().decode().strip())

# Send command
ser.write(b"SET 42\n")

# Read response
response = ser.readline().decode().strip()
print("Board says:", response)

ser.close()
