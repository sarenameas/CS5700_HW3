import udt
import config
import util
import timer
import time
import struct

# Go-Back-N reliable transport protocol.
class GoBackN:
  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.base = 1
    self.nextseqnum = 1
    self.sendpkt = [b'']*config.WINDOWN_SIZE
    self.expectedseqnum = 1
    self.recvr_segment = util.make_segment(config.MSG_TYPE_ACK, 0, b'')
    # Starts the timer thread immediately upon object creating
    self.timer = timer.TimerThread(self.timeout_handler)

  # "send" is called by application. Return true on success, false
  # otherwise.
  def send(self, msg):
    if self.nextseqnum < (self.base + config.WINDOWN_SIZE):
      self.sendpkt[self.nextseqnum - self.base] = util.make_segment(config.MSG_TYPE_DATA, self.nextseqnum, msg)
      self.network_layer.send(self.sendpkt[self.nextseqnum - self.base])
      if self.base == self.nextseqnum:
        self.timer.stop()
        self.timer.start()
      self.nextseqnum += 1
    else:
      return False
    return True

  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    if not util.is_corrupt(msg):
      seqnum = util.get_seq(msg)
      # Sender actions are for ACK packets
      if util.is_ack(msg, seqnum):
        if config.DEBUG: print("Received ACK, ", seqnum)
        oldbase = self.base
        self.base = seqnum + 1
        # Moving the base means shifting the list
        self.sendpkt = self.sendpkt[self.base - oldbase:] + [b''] * (self.base - oldbase)
        if (self.base == self.nextseqnum):
          self.timer.stop()
        else:
          self.timer.stop()
          self.timer.start()
      # Reciver actions are for DATA packets
      elif util.has_seq(msg, self.expectedseqnum): 
        if config.DEBUG: print("Received DATA, ", seqnum)
        payload = util.extract(msg)
        self.msg_handler(payload)
        self.recvr_segment = util.make_segment(config.MSG_TYPE_ACK, self.expectedseqnum, b'')
        self.network_layer.send(self.recvr_segment)
        self.expectedseqnum += 1
      # Received out of order sequence
      else:
        if config.DEBUG: 
          print("Out of order packet received, seqnum = ", seqnum)
          if struct.unpack('!H', msg[:2])[0] == config.MSG_TYPE_DATA:
            print("Expectedseqnum = ", self.expectedseqnum)
    else:
      if config.DEBUG: print("Corrupt packet received")
      
    # Receiver always sends an ack for the last successful packet received
    if struct.unpack('!H', msg[:2])[0] == config.MSG_TYPE_DATA:
      self.network_layer.send(self.recvr_segment)
  # end handle_arrival_msg()
  
  # "handler" to be called by the timer when it times out.
  def timeout_handler(self):
    snapshot = []
    for pkt in self.sendpkt:
      if pkt != b'':
        snapshot.append('w')
      else:
        snapshot.append('x')
    if config.DEBUG:
      print("Timeout: window: ", snapshot)
      print("Timeout: base = ", self.base)
      print("Timeout: nextseqnum = ", self.nextseqnum)
    for pkt in self.sendpkt[:(self.nextseqnum-self.base)]:
      self.network_layer.send(pkt)
    self.timer.stop()
    self.timer.start()

  # Cleanup resources.
  def shutdown(self):
    while self.base != self.nextseqnum: pass
    self.timer.exit()
    self.network_layer.shutdown()
