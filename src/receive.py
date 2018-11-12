import wave
import numpy.fft, pyaudio
import config, codec


def analyse_bit(samples):
    """
    Determines if the input data represents a 0 or a 1.
    :param samples:
    :return: (bit, signal, noise)
    """

    assert len(samples) == config.SYMBOL_SIZE

    # apply a hamming window to the input
    samples *= numpy.hamming(len(samples))

    # compute the fft over our input
    fft_result = numpy.fft.rfft(samples, norm="ortho")

    # find the closest fft bin to our frequency
    freq_0 = int((config.SYMBOL_SIZE * config.FREQ_0) / config.RATE)
    freq_1 = int((config.SYMBOL_SIZE * config.FREQ_1) / config.RATE)

    # find the amplitude for each frequency
    amp_0 = abs(fft_result[freq_0])
    amp_1 = abs(fft_result[freq_1])

    if amp_0 > amp_1:
        bit, signal, noise = 0, amp_0, amp_1
    else:
        bit, signal, noise = 1, amp_1, amp_0

    return bit, signal, noise


def detect_sync_word(samples, expected_bits):

    # we should have exactly enough samples to make 1 sync word
    samples_bits_len = len(samples) / config.SYMBOL_SIZE
    expected_bits_len = len(expected_bits)
    assert samples_bits_len == expected_bits_len

    signal_amps = []
    noise_amps = []

    for i in range(expected_bits_len):

        start = i * config.SYMBOL_SIZE
        end = start + config.SYMBOL_SIZE
        window = samples[start:end]

        assert len(window) == config.SYMBOL_SIZE

        bit, signal, noise = analyse_bit(window)

        signal_amps.append(signal)
        noise_amps.append(noise)

        if bit != expected_bits[i]:
            # the bits don't match, abort
            return False, 0.0

    snr = sum(signal_amps) / sum(noise_amps)

    return True, snr


def decode_8bits(samples):
    samples_bits_len = len(samples) / config.SYMBOL_SIZE
    # sanity check
    assert samples_bits_len == 8, "decode_8bits received incorrect number of samples %s != %s" % (samples_bits_len, 8)

    bits = []
    signal_amps = []
    noise_amps = []

    for i in range(samples_bits_len):

        start = i * config.SYMBOL_SIZE
        end = start + config.SYMBOL_SIZE
        window = samples[start:end]

        bit, signal, noise = analyse_bit(window)

        signal_amps.append(signal)
        noise_amps.append(noise)

        bits.append(bit)

    snr = sum(signal_amps) / sum(noise_amps)

    return bits, snr


def chunked_read_frame(data, stream):

    # how many samples do we need to reach the next byte?
    remaining_samples_to_8bit = (8 * config.SYMBOL_SIZE) - len(data)

    # sanity check
    assert remaining_samples_to_8bit > 0

    # read however many asmples we need to complete an 8 bit word
    remaining_buffer = stream.read(remaining_samples_to_8bit)
    remaining_buffer = codec.decode_int16(remaining_buffer)

    # add that to our frame, so the total number of samples is equal to 8 bits when decoded
    data = numpy.append(data, remaining_buffer)

    # decode our first byte
    bits, snr = decode_8bits(data)
    string = codec.bits_to_string(bits)

    # we'll gradually add bytes to our decoded_frame as we read them from the audio stream
    decoded_frame = ""

    # add our first byte to the decoded_frame
    decoded_frame += string

    # keep track of how many bits we've read so far
    bits_read = 8

    # how many bits we'll need to read in total
    total_bits = len(config.FRAME_DATA) * 8

    while bits_read < total_bits:

        # read 1 bytes worth of samples from the audio stream and decode it
        data = stream.read(config.SYMBOL_SIZE * 8)
        data = codec.decode_int16(data)
        bits, snr = decode_8bits(data)
        string = codec.bits_to_string(bits)

        # add decoded byte to decoded frame
        decoded_frame += string

        # keep track of how many bits we've read so far
        bits_read += 8

    return decoded_frame


class WaveStream(object):

    def __init__(self, filename):
        self.stream = wave.open(filename, "rb")
        print(filename)
        print("  sample_width=%s" % self.stream.getsampwidth())
        print("  channels=%s" % self.stream.getnchannels())
        print("  rate=%s" % self.stream.getframerate())

    def read(self, n):
        return self.stream.readframes(n)

    def close(self):
        return self.stream.close()


def main():

    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=config.RATE, input=True)
    # stream = WaveStream("/Users/rfc/Desktop/syncword_xyz.wav")

    # Our input buffer will be the size of the sync word, plus 1 extra bit.
    # This way we have 1 symbols worth of extra space to scan.
    #
    extra_bits = 1
    bits_per_syncword = len(config.SYNC_WORD) * 8
    bits_per_buffer = bits_per_syncword + extra_bits
    buffer_size = bits_per_buffer * config.SYMBOL_SIZE
    samples_per_syncword = bits_per_syncword * config.SYMBOL_SIZE

    expected_bits = codec.string_to_bits(config.SYNC_WORD)

    scan_space = buffer_size - samples_per_syncword

    data = stream.read(buffer_size)
    data = codec.decode_int16(data)

    assert len(data) == buffer_size

    print(len(data) / config.SYMBOL_SIZE, bits_per_syncword)

    print("receive: scan_space={scan_space}".format(scan_space=scan_space))

    while True:

        # the number of decoded samples should be equal to the buffer size
        assert len(data) == buffer_size

        assert scan_space > 0

        # the amount of scan space should be `extra_bits` symbols
        assert scan_space == (config.SYMBOL_SIZE * extra_bits)

        found_frame = False

        for i in range(0, scan_space, config.SKIP_SAMPLES):

            window = data[i:i+samples_per_syncword]

            detected, snr = detect_sync_word(window, expected_bits)
            if detected:
                if snr >= config.SNR_MIN:
                    # print("detected: %s (%s)" % (i, snr))
                    frame = chunked_read_frame(data[i+samples_per_syncword:], stream)
                    print("[snr=%4s] '%s'" % (str(snr)[:4], frame))
                    found_frame = True
                    break
                else:
                    # too noisey
                    continue

        if found_frame:
            # if we found a frame, fill up the buffer with enough samples to detect a sync word
            data = stream.read(buffer_size)
            data = codec.decode_int16(data)
        else:
            # otherwise read the next chunk of samples
            next_buffer_size = config.BUFFER_SIZE
            next_buffer = stream.read(next_buffer_size, exception_on_overflow=True)
            next_buffer = codec.decode_int16(next_buffer)
            data = numpy.append(data[next_buffer_size:], next_buffer)

    stream.close()


if __name__ == "__main__":
    main()
