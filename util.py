import dummy
import gbn
import ss
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
def get_checksum(segment):
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