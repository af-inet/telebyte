import pyaudio
import numpy


def chunked(iterator, chunk_size):
    chunk = []
    for item in iterator:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def signal(duration, rate):
    x = 0.0
    frequency = 0.0
    nyquist = rate / 2
    while frequency < nyquist:
        frequency += 1.0 / duration / rate
        f = int(frequency)
        x += f * 2 * numpy.pi / rate
        y = numpy.sin(x)
        print(f)
        yield y


def main():
    rate = 44100
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=rate, output=True)
    s = signal(0.01, rate)
    chunks = chunked(s, 1024)
    int16_max = numpy.iinfo(numpy.int16).max
    for chunk in chunks:
        data = (numpy.array(chunk) * int16_max).astype(numpy.int16).tobytes()
        stream.write(data)


main()