import struct
import serial

class LED(object):
  """sets RGB values for LED via Arduino-mediated TLC5940"""
  def __init__(self, serial_device, speed=115200):
    super(LED, self).__init__()
    self.serial = serial.Serial(serial_device, speed)

  def send_reset(self):
    self.serial.write(0xff)
    self.serial.write(0xff)

  def set(self, r, g, b):
    r = min(r, 4095)
    self.serial.write(b'R')
    self.serial.write(struct.pack('>H', r))

    g = min(g, 4095)
    self.serial.write(b'G')
    self.serial.write(struct.pack('>H', g))

    b = min(b, 4095)
    self.serial.write(b'B')
    self.serial.write(struct.pack('>H', b))

    self.serial.flush()
