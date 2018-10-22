#
# codec - functions for encoding / decoding data.
#
import array
import numpy


INT16_MAX = 32767


def unpack_int16_array(data):
    arr = array.array('h')
    arr.fromstring(data)
    return arr


def unpack_int16_numpy(data):
    return numpy.frombuffer(data, dtype=numpy.int16)


def unpack_int16(data):
    return unpack_int16_numpy(data)


def normalize_int16(data):
    values = [float(value) / float(INT16_MAX) for value in data]
    return values


def denormalize_int16(value):
    return int(float(value) * float(INT16_MAX))


def pack_int16_array(values):
    try:
        return array.array('h', values).tostring()
    except OverflowError:
        for i, value in enumerate(values):
            if value > INT16_MAX:
                # It is nice to know which int caused the error.
                raise OverflowError("values[%s] (%s) > %s" % (i, value, INT16_MAX))
        raise


def pack_int16_numpy(values):
    assert values.dtype == numpy.dtype('int16')
    return array.tobytes()


def pack_int16(values):
    return pack_int16_numpy(values)


def encode_int16(values):
    return (values * INT16_MAX).astype(numpy.int16).tobytes()


def decode_int16(values):
    return numpy.frombuffer(values, dtype=numpy.int16).astype(numpy.float) / INT16_MAX


def bits_to_byte(bits):
    byte = 0
    for i, bit in enumerate(reversed(bits)):
        byte |= int(bool(bit)) << i
    return byte


def byte_to_bits(byte):
    bits = [
        (byte & (1 << i)) >> i
        for i in range(8)
    ]
    return list(reversed(bits))


def string_to_bits(string):
    bits = []
    for char in string:
        bits += byte_to_bits(ord(char))
    return bits


def bits_to_string(bits):

    # number of bits should be divisible by 8, since there's 8 bits in a char
    assert ((len(bits) % 8) == 0)

    word_count = int(len(bits) / 8)
    string = b''

    for i in range(word_count):
        word = bits[i*8:(i*8)+8]
        byte = bits_to_byte(word)
        char = bytes(chr(byte), encoding='utf-8')
        string += char

    return string.decode("utf-8")
