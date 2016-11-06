import udt
import config
import struct
import util
from enum import Enum
from threading import Timer

# Define the sender and reciver states
class State(Enum):
  SEQ_0 = 0 # Waiting for call 0 from above
  SEQ_1 = 1 # Waiting for call 1 from above
  ACK_0 = 2 # Waiting for ACK 0
  ACK_1 = 3 # Waiting for ACK 1


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
  # Define the sender/reciever states
  send_state
  recv_state
  # Define the current segment
  segment
  # Define once through, first segment recived
  oncethru

  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    # The initial state for the sender is wait for seq 0 from above
    self.send_state = State.SEQ_0
    # The initial state for the reciever is wait for seq 0 from below
    self.recv_state = State.SEQ_0
    self.segment = b''
    self.oncethru = 0


  # "send" is called by application. Return true on success, false
  # otherwise.
  def send(self, msg):
    # TODO: impl protocol to send packet from application layer.
    # call self.network_layer.send() to send to network layer.
    if (self.send_state == State.ACK_0 or self.send_state == State.ACK_1):
      return False
    else:
      # Create the segment with the proper header
      type = config.MSG_TYPE_DATA
      sequence = self.send_state
      btype = struct.pack('!H', type)
      bsequence = struct.pack('!H', sequence)
      bpayload = msg.encode()
      bchecksum = util.get_checksum(btype + bsequence + bpayload)
      self.segment = btype + bsequence + bchecksum + bpayload

      if self.send_state == State.SEQ_0:
        self.send_state = State.ACK_0
      else:
        self.send_state = State.ACK_1
      
      # Start the timer
      timer_thread = Timer(config.TIMEOUT_MSEC * (0.001), self.handle_timeout)
      timer_thread.start()
      # Send the segment into the network
      self.network_layer.send(self.segment)
    return True


  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    
    if self.send_state == State.ACK_0: 
      if (not is_corrupt(msg)) and is_ack(msg, 0):
        self.send_state = State.SEQ_1
    elif self.send_state == State.ACK_1:
      if (not is_corrupt(msg)) and is_ack(msg, 0):
        self.send_state = State.SEQ_0
    elif self.recv_state == State.SEQ_0 or self.recv_state == State.SEQ_1:
      if (not is_corrupt(msg)) and has_seq(msg, self.recv_state):
        payload = util.extract(msg)
        self.msg_handle(payload)
        self.segment = util.make_segment(config.MSG_TYPE_ACK, self.recv_state)
        self.network_layer.send(self.segment)
        self.oncethru = 1
      else:
        if oncethru == 1:
          self.network_layer.send(self.segment)


  # "handler" to be called by the timer threads
  def handle_timeout(self):
    # Start the timer
    timer_thread = Timer(config.TIMEOUT_MSEC * (0.001), self.handle_timeout)
    timer_thread.start()
    # Send the segment into the network
    self.network_layer.send(self.segment)
      

  # Cleanup resources.
  def shutdown(self):
    # TODO: cleanup anything else you may have when implementing this
    # class.
    self.network_layer.shutdown()
