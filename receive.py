import numpy.fft, pyaudio
import config, codec
import wave


def maxindex(values):
    index = 0
    result = abs(values[index])
    for i, value in enumerate(values):
        if abs(value) > result:
            index = i
            result = abs(value)
    return index, result


def detect_sync_word(samples, expected_bits):

    # we should have exactly enough samples to make 1 sync word
    samples_bits_len = len(samples) / config.SYMBOL_SIZE
    expected_bits_len = len(expected_bits)
    assert samples_bits_len == expected_bits_len

    freq_0 = int((config.SYMBOL_SIZE * config.FREQ_0) / config.RATE)
    freq_1 = int((config.SYMBOL_SIZE * config.FREQ_1) / config.RATE)

    signal_amps = []
    noise_amps = []

    for i in range(expected_bits_len):

        start = i * config.SYMBOL_SIZE
        end = start + config.SYMBOL_SIZE
        window = samples[start:end]

        assert len(window) == config.SYMBOL_SIZE

        # window *= numpy.hamming(len(window))
        fft_result = numpy.fft.rfft(window, norm="ortho")

        amp_0 = abs(fft_result[freq_0])
        amp_1 = abs(fft_result[freq_1])

        if amp_0 > amp_1:
            bit = 0
            signal_amps.append(amp_0)
            noise_amps.append(amp_1)
        else:
            bit = 1
            signal_amps.append(amp_1)
            noise_amps.append(amp_0)

        if bit != expected_bits[i]:
            # the bits don't match, abort
            return False, 0.0

    snr = sum(signal_amps) / sum(noise_amps)

    return True, snr


def decode_frame(samples):

    samples_bits_len = len(samples) / config.SYMBOL_SIZE
    assert samples_bits_len == config.FRAME_SIZE

    freq_0 = int((config.SYMBOL_SIZE * config.FREQ_0) / config.RATE)
    freq_1 = int((config.SYMBOL_SIZE * config.FREQ_1) / config.RATE)

    bits = []
    signal_amps = []
    noise_amps = []

    for i in range(config.FRAME_SIZE):

        start = i * config.SYMBOL_SIZE
        end = start + config.SYMBOL_SIZE
        window = samples[start:end]

        assert len(window) == config.SYMBOL_SIZE

        window *= numpy.hamming(len(window))
        fft_result = numpy.fft.rfft(window, norm="ortho")

        amp_0 = abs(fft_result[freq_0])
        amp_1 = abs(fft_result[freq_1])

        if amp_0 > amp_1:
            bit = 0
            signal_amps.append(amp_0)
            noise_amps.append(amp_1)
        else:
            bit = 1
            signal_amps.append(amp_1)
            noise_amps.append(amp_0)

        bits.append(bit)

    snr = sum(signal_amps) / sum(noise_amps)

    return bits, snr


def read_frame(data, stream):
    remaining_samples = ((len(config.FRAME_DATA) * 8) * config.SYMBOL_SIZE) - len(data)
    remaining_buffer = stream.read(remaining_samples)
    remaining_buffer = codec.decode_int16(remaining_buffer)
    data = numpy.append(data, remaining_buffer)
    bits, snr = decode_frame(data)
    string = codec.bits_to_string(bits)
    print("frame: [%s] %s" % (string, snr))


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

    # stream.read(1024 * 20)
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

        for i in range(0, scan_space, 40):

            start = i
            end = i + samples_per_syncword
            window = data[start:end]

            detected, snr = detect_sync_word(window, expected_bits)
            if detected:
                if snr >= 5.0:
                    print("detected: %s (%s)" % (i, snr))
                    read_frame(data[end:], stream)
                    data = stream.read(buffer_size)
                    data = codec.decode_int16(data)
                    break
                else:
                    # too noisey
                    continue

        next_buffer_size = 256
        next_buffer = stream.read(next_buffer_size)
        next_buffer = codec.decode_int16(next_buffer)

        data = numpy.append(data[next_buffer_size:], next_buffer)

    stream.close()


if __name__ == "__main__":
    main()
