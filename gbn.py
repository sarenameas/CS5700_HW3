import udt
import config
import util
import timer

# Go-Back-N reliable transport protocol.
class GoBackN:
  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.base = 1
    self.nextseqnum = 1
    self.sendpkt = []
    self.expectedseqnum = 1
    # Starts the timer thread immediately upon object creating
    self.timer = timer.TimerThread(self.timeout_handler)

  # "send" is called by application. Return true on success, false
  # otherwise.
  def send(self, msg):
    if self.nextseqnum < (self.base + config.WINDOWN_SIZE):
      sendpkt[nextseqnum - base] = util.make_segment(config.MSG_TYPE_DATA, self.nextseqnum, msg)
      self.network_layer.send()
      if base == nextseqnum:
        self.timer.start()
      nextseqnum += 1
    else:
      return False

  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    if not util.is_corrupt(msg):
      seqnum = util.get_seq(msg)
      # Sender actions are for ACK packets
      if util.is_ack(msg, seqnum):
        self.base = seqnum + 1
        if (self.base == self.nextseqnum):
          self.timer.stop()
        else:
          self.timer.stop()
          self.timer.start()
      # Reciver actions are for DATA packets
      if util.is_seq(msg, self.expectedseqnum): 
        payload = util.extract(msg)
        self.msg_handler(payload)
        segment = make_segment(config.MSG_TYPE_ACK, self.expectedseqnum)
        self.network_layer.send(segment)
        self.expectedseqnum += 1
  
  # "handler" to be called by the timer when it times out.
  def timeout_handler(self):
    self.timer.start()
    for pkt in sendpkt[self.base:self.nextseqnum]:
      self.network_layer.send(pkt)

  # Cleanup resources.
  def shutdown(self):
    self.timer.exit()
    self.network_layer.shutdown()
