import codec
import array
import numpy
import numpy.testing
import timeit
import receive, send
import config


original = range(0, 100)
encoded = array.array('h', original).tostring()


def test_codec_array():

    decoded = codec.unpack_int16_array(encoded)

    numpy.testing.assert_array_equal(
        numpy.array(original),
        numpy.array(decoded)
    )


def test_codec_numpy():

    decoded = codec.unpack_int16_numpy(encoded)

    numpy.testing.assert_array_equal(
        numpy.array(original),
        numpy.array(decoded)
    )


def test_sync_word():

    # test detecting a syncword in a noiseless environemnt

    signal_0 = send.make_signal(config.FREQ_0, config.RATE, config.SYMBOL_SIZE)
    signal_1 = send.make_signal(config.FREQ_1, config.RATE, config.SYMBOL_SIZE)

    assert len(signal_0) == config.SYMBOL_SIZE
    assert len(signal_1) == config.SYMBOL_SIZE

    bits = codec.string_to_bits(config.SYNC_WORD)

    full_signal = numpy.array([signal_0 if bit == 0 else signal_1
                               for bit in bits]).flatten()

    assert receive.detect_sync_word(full_signal, bits)


def benchmark_codec():

    # testing shows that numpy's decode seems to be around 2x faster than array, when given a large array (>10000 items)

    setup = """
import array, codec
original = range(0, 10000)
encoded = array.array('h', original).tostring()
    """

    t_array = timeit.timeit("codec.unpack_int16_array(encoded)", setup=setup, number=100000)

    t_numpy = timeit.timeit("codec.unpack_int16_numpy(encoded)", setup=setup, number=100000)

    print("array: %s" % t_array)
    print("numpy: %s" % t_numpy)


def main():
    test_codec_array()
    test_codec_numpy()
    test_sync_word()
    benchmark_codec()


if __name__ == '__main__':
    main()
