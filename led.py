import serial

class LED(object):
  """sets RGB values for LED via Arduino-mediated TLC5940"""
  def __init__(self, serial_device, speed=115200):
    super(LED, self).__init__()
    self.serial = serial.Serial(serial_device, speed)

  def _get_bytes(self, value):
    b1 = (0b0000111100000000 & value) >> 8
    b2 = (0b0000000011111111 & value)
    return (chr(b1), chr(b2))

  def send_reset(self):
    self.serial.write(chr(0b11111111))
    self.serial.write(chr(0b11111111))

  def set(self, r, g, b):
    self.serial.write(b'R')
    x = self._get_bytes(r)
    self.serial.write(x[0].encode('ascii'))
    self.serial.write(x[1].encode('ascii'))

    self.serial.write(b'G')
    x = self._get_bytes(g)
    self.serial.write(x[0].encode('ascii'))
    self.serial.write(x[1].encode('ascii'))

    self.serial.write(b'B')
    x = self._get_bytes(b)
    self.serial.write(x[0].encode('ascii'))
    self.serial.write(x[1].encode('ascii'))

