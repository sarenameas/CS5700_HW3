import dummy
import gbn
import ss
import config
import struct


def get_transport_layer_by_name(name, local_port, remote_port, msg_handler):
  assert name == 'dummy' or name == 'ss' or name == 'gbn'
  if name == 'dummy':
    return dummy.DummyTransportLayer(local_port, remote_port, msg_handler)
  if name == 'ss':
    return ss.StopAndWait(local_port, remote_port, msg_handler)
  if name == 'gbn':
    return gbn.GoBackN(local_port, remote_port, msg_handler)

# Calculates the checksum of the input segment bytes in big endian. Returns 
# the 16 bit checksum.
def make_checksum(segment):
  padded_segment = segment + bytes(len(segment) % 2)
  words = [padded_segment[i:i+2] for i in range(0, len(padded_segment), 2)]
  shorts = [struct.unpack('!H', word)[0] for word in words]
  MAXSHORT = pow(2,16) - 1
  sum = 0
  for short in shorts:
    sum = sum + short
    # Wrap overflow
    if sum > MAXSHORT:
      sum = sum & MAXSHORT
      sum += 1
  checksum = ~sum
  # truncate the integer byte represenation to a short
  bchecksum = struct.pack('!i', checksum)[-2:]
  return bchecksum

# Dermines if the input segment is corrupt. Returns True if it is, False
# otherwise.
def is_corrupt(segment):
  padded_segment = segment + bytes(len(segment) % 2)
  words = [padded_segment[i:i+2] for i in range(0, len(padded_segment), 2)]
  shorts = [struct.unpack('!H', word)[0] for word in words]
  MAXSHORT = pow(2,16) - 1
  sum = 0
  for short in shorts:
    sum = sum + short
  
  if sum == MAXSHORT:
    return False
  return True

# Determine if the input segment is an ACK segment. Returns True of the 
# segment is and ACK segment and has the given expected_sequence, false 
# otherwise. 
def is_ack(segment, expected_sequence):
  type = struct.unpack('!H', segment[:2])[0]
  sequence = struct.unpack('!H', segment[2:4])[0]
  if type == config.MSG_TYPE_ACK and sequence == expected_sequence:
    return True
  else:
    return False

# Determind if the input segment is a data segment with the expected 
# sequence number.
def has_seq(segment, expected_sequence):
  type = struct.unpack('!H', segment[:2])[0]
  sequence = struct.unpack('!H', segment[2:4])[0]
  if type == config.MSG_TYPE_DATA and sequence == expected_sequence:
    return True
  else:
    return False

# Create a segment from the given message type, sequence number, and input 
# payload. Returns the segment in bytes.
def make_segment(msg_type, sequence, payload):
  bmsg_type = struct.pack('!H', msg_type)
  bsequence = struct.pack('!H', sequence)
  bpayload = payload
  if type(payload) is str:
    bpayload = payload.encode()
  bchecksum = make_checksum(bmsg_type + bsequence + bpayload)
  segment = bmsg_type + bsequence + bchecksum + bpayload
  return segment

# Extracts and returns the payload from the input segment.
def extract(segment):
  payload = segment[6:].decode()
  return payload

# Get the sequence number from the pack.import
def get_seq(segment):
  return struct.unpack('!h', segment[2:4])[0]

    