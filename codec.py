#
# codec - functions for encoding / decoding data.
#
import array


INT16_MAX = 32767


def normalize16(value):
    return float(value) / float(INT16_MAX)


def unpack16(string):
    arr = array.array('h')
    arr.fromstring(string)
    return arr


def decode16(data):
    unpacked_values = unpack16(data)
    normalized_values = map(normalize16, unpacked_values)
    return normalized_values


def denormalize16(value):
    return int(float(value) * float(INT16_MAX))


def pack16(values):
    try:
        return array.array('h', values).tostring()
    except OverflowError:
        for i, value in enumerate(values):
            if value > INT16_MAX:
                # It is nice to know which int caused the error.
                raise OverflowError("values[%s] (%s) > %s" % (i, value, INT16_MAX))
        raise


def encode16(values):
    values = map(denormalize16, values)
    data = pack16(values)
    return data


def bits_to_byte(bits):
    byte = 0
    for i, bit in enumerate(reversed(bits)):
        byte |= int(bool(bit)) << i
    return byte


def bits_to_string(bits):

    # number of bits should be divisible by 8, since there's 8 bits in a char
    assert ((len(bits) % 8) == 0)

    word_count = len(bits) / 8
    string = b''

    for i in range(word_count):
        word = bits[i*8:(i*8)+8]
        byte = bits_to_byte(word)
        char = chr(byte)
        string += char

    return string
