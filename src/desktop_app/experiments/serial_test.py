import serial
import time

PORT = "COM4"  # or /dev/ttyUSB0, /dev/tty.usbmodemXXXX
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)  # let board reset

for i in range(10):
    # Read startup message
    print(ser.readline().decode().strip())

    # Send command
    ser.write(f"SET {i}\n".encode("utf-8"))

    # Read response
    response = ser.readline().decode().strip()
    print("Board says:", response)

ser.close()
