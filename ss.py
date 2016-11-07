import udt
import config
import struct
import util
import timer
from enum import IntEnum
from threading import Lock

# Define the sender and reciver states
class State(IntEnum):
  SEQ_0 = 0 # Waiting for call 0 from above
  SEQ_1 = 1 # Waiting for call 1 from above
  ACK_0 = 2 # Waiting for ACK 0
  ACK_1 = 3 # Waiting for ACK 1


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    # The initial state for the sender is wait for seq 0 from above
    self.send_state = State.SEQ_0
    # The initial state for the reciever is wait for seq 0 from below
    self.recv_state = State.SEQ_0
    # Initally empty transport layer segment
    self.segment = b''
    # Locking of segment
    self.segment_lock = Lock()
    # Once through for reciver
    self.oncethru = 0
    # Define timer thread, creates thread immediately
    self.timer = timer.TimerThread(self.handle_timeout)


  # "send" is called by application. Return true on success, false
  # otherwise.
  def send(self, msg):
    if (self.send_state == State.ACK_0 or self.send_state == State.ACK_1):
      return False
    else:
      # Create the segment with the proper header
      self.segment_lock.acquire()
      self.segment = util.make_segment(config.MSG_TYPE_DATA, self.send_state, msg)
      self.segment_lock.release()

      # Update the state of this protocol
      if self.send_state == State.SEQ_0:
        self.send_state = State.ACK_0
      else:
        self.send_state = State.ACK_1

      # Send the segment into the network
      self.network_layer.send(self.segment)
            
      # Start the timer
      self.timer.start()
    return True


  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    
    if self.send_state == State.ACK_0: 
      if (not util.is_corrupt(msg)) and util.is_ack(msg, 0):
        # Make sure the timer is stopped upon transition to waiting for 
        # messages from above.
        self.timer.stop()
        self.send_state = State.SEQ_1
    elif self.send_state == State.ACK_1:
      if (not util.is_corrupt(msg)) and util.is_ack(msg, 1):
        self.timer.stop()
        self.send_state = State.SEQ_0
    elif self.recv_state == State.SEQ_0:
      if (not util.is_corrupt(msg)) and util.has_seq(msg, self.recv_state.value):
        payload = util.extract(msg)
        self.msg_handler(payload)
        self.segment = util.make_segment(config.MSG_TYPE_ACK, self.recv_state.value, b'')
        self.oncethru = 1
        self.recv_state = State.SEQ_1
      if self.oncethru == 1:
        self.network_layer.send(self.segment)
    elif self.recv_state == State.SEQ_1:
      if (not util.is_corrupt(msg)) and util.has_seq(msg, self.recv_state.value):
        payload = util.extract(msg)
        self.msg_handler(payload)
        self.segment = util.make_segment(config.MSG_TYPE_ACK, self.recv_state.value, b'')
        self.recv_state = State.SEQ_0
      self.network_layer.send(self.segment)

  # "handler" to be called by the timer threads
  def handle_timeout(self):
    # Send the segment into the network
    self.segment_lock.acquire()
    self.network_layer.send(self.segment)
    self.segment_lock.release()
    # Start the Timer
    self.timer.start()    

  # Cleanup resources.
  def shutdown(self):
    # TODO: cleanup anything else you may have when implementing this
    # class.
    self.network_layer.shutdown()
