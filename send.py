import numpy
import numpy as np
import numpy.fft
import pyaudio
import config, codec



def flatten(lists):
    return [item for _list in lists for item in _list]


def byte_to_bits(byte):
    bits = [
        (byte >> i) & 1
        for i in reversed(range(8))
    ]
    return bits


def random_linspace(end, count):
    array = np.arange()
    return array


def make_signal(frequency, rate, buffer_size):

    samples_per_wave = float(rate) / float(frequency)

    waves_per_buffer = buffer_size / samples_per_wave
    waves_per_buffer = np.floor(waves_per_buffer)

    actual_space = samples_per_wave * waves_per_buffer

    extra_space = np.linspace(0, 0, buffer_size - actual_space)

    # num_of_samples = waves_per_buffer * samples_per_wave
    xs = np.linspace(0, actual_space, actual_space) * numpy.pi * 2 * waves_per_buffer
    xs = np.append(xs, extra_space)
    ys = np.sin(xs)
    # ys = [(n * (1.0 - (0.01 * np.random.rand(1)[0]))) for n in ys]

    # ys *= np.hamming(len(ys))

    print(
        " ".join([
            "frequency= %.2f" % frequency,
            "length= %.2f (%.2f)" % (len(ys), float(len(ys)) / float(rate)),
            "samples_per_wave= %.2f" % samples_per_wave,
            "waves_per_buffer= %.2f" % waves_per_buffer,
            # "num_of_samples= %.2f (%.2f)" % (num_of_samples, float(num_of_samples) / float(rate)),
            "zeros= %.2f (%.2f)" % (len(extra_space), len(extra_space) / float(rate)),
            "first= %.2f" % ys[0],
            "last= %.2f" % ys[-1],
            "buffer_size= %.2f" % buffer_size,
        ])
    )

    return ys


def empty():
    ys = numpy.linspace(0, 0, config.RATE)
    return ys


def main():

    msg = config.SYNC_WORD

    signal_0 = make_signal(config.FREQ_0, config.RATE, config.SYMBOL_SIZE)
    signal_1 = make_signal(config.FREQ_1, config.RATE, config.SYMBOL_SIZE)

    silence = empty()

    pa = pyaudio.PyAudio()

    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=config.RATE,
                     output=True)

    stream.write(silence)

    for char in msg:
        for bit in byte_to_bits(ord(char)):
            message = codec.encode16(signal_1 if bit else signal_0)
            stream.write(message)

    for char in config.FRAME_DATA:
        bits = byte_to_bits(ord(char))
        print(bits)
        for bit in bits:
            message = codec.encode16(signal_1 if bit else signal_0)
            stream.write(message)

    # if you don't end with silence, the program will end before the audio stream does
    stream.write(silence)
    stream.write(silence)


if __name__ == '__main__':
    main()