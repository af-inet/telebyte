import numpy
import numpy as np
import numpy.fft
import pyaudio
import config, codec
import datetime


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

    samples_per_wave = np.floor(float(rate) / float(frequency))

    waves_per_buffer = float(buffer_size) / float(samples_per_wave)
    waves_per_buffer = np.floor(waves_per_buffer)

    actual_space = samples_per_wave * waves_per_buffer

    extra_space = np.linspace(0, 0, int(buffer_size - actual_space))

    xs = np.linspace(0, int(actual_space), int(actual_space)) * numpy.pi * 2 * waves_per_buffer
    ys = np.sin(xs)
    ys = np.append(extra_space, ys)

    assert len(ys) == buffer_size

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


def init_frame(data):
    assert len(data) < len(config.FRAME_DATA)
    space = len(config.FRAME_DATA) - len(data)
    frame = data + (" " * space)
    return frame


def main():

    signal_0 = make_signal(config.FREQ_0, config.RATE, config.SYMBOL_SIZE)
    signal_1 = make_signal(config.FREQ_1, config.RATE, config.SYMBOL_SIZE)

    silence = empty()

    pa = pyaudio.PyAudio()

    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=config.RATE,
                     output=True)

    for _ in range(4):
        stream.write(silence)

    for i in range(16):

        # write the sync word
        for char in config.SYNC_WORD:
            for bit in byte_to_bits(ord(char)):
                message = codec.encode_int16(signal_1 if bit else signal_0)
                assert (len(message) / 2) == config.SYMBOL_SIZE
                stream.write(message)

        # write the message
        now = str(datetime.datetime.now())
        frame = init_frame(now)
        frame = str(i) + " " + frame
        frame = frame[:len(config.FRAME_DATA)]

        for char in frame:
            bits = byte_to_bits(ord(char))
            for bit in bits:
                message = codec.encode_int16(signal_1 if bit else signal_0)
                stream.write(message)

        print("sent: %s" % frame)

    for _ in range(4):
        stream.write(silence)
    stream.stop_stream()
    stream.close()
    pa.terminate()


if __name__ == '__main__':
    main()