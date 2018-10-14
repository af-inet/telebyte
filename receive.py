import array, string, wave, math
from functools import wraps
from time import time
import numpy.fft
import pyaudio
import traceback
import config
import codec
import collections
import threading

from contextlib import contextmanager
import time
import logging


@contextmanager
def timed(prefix=""):
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        elapsed_seconds = "%.7f" % float(end - start)
        print('%s: elapsed seconds: %s' % (prefix, elapsed_seconds))


class State(object):
    def __init__(self, maxlen):
        self.ring = collections.deque(maxlen=maxlen)
        self.running = True


def open_stream():
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=config.RATE,
                     input=True)
    return stream


def flatten(buckets):
    return [item for bucket in buckets for item in bucket]


def printable(s):
    return b''.join([c if c in string.printable else '_' for c in s])


def batch(iterator, n=1):
    batch = []
    for item in iterator:
        batch.append(item)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch


def maxindex(values):
    index = 0
    result = abs(values[index])
    for i, value in enumerate(values):
        if abs(value) > result:
            index = i
            result = abs(value)
    return index, result


def calculate_signal_to_noise(fft_frames):
    noise_amps = []
    signal_amps = []

    for frame in fft_frames:
        amp0 = abs(frame[config.FREQ_0])
        amp1 = abs(frame[config.FREQ_1])
        if amp0 > amp1:
            noise_amps.append(amp1)
            signal_amps.append(amp0)
        else:
            noise_amps.append(amp0)
            signal_amps.append(amp1)

    return sum(signal_amps) / sum(noise_amps)


def detect_sync_word(data, scan_count):
    """
    Returns an offset in bytes where the Sync Word may be decoded,
    Returns None if the Sync Word was not found.
    """

    # make sure the sync word will actually fit inside this buffer
    assert (len(data) > config.SYNC_WORD_SIZE)

    scan_space = len(data) - config.SYNC_WORD_SIZE
    scan_length = int(numpy.floor(scan_space / float(scan_count)))

    for i in range(scan_count):

        start = int(numpy.floor(i * scan_length))
        end = int(start + config.SYNC_WORD_SIZE)
        chunk = data[start:end]

        if len(chunk) != config.SYNC_WORD_SIZE:
            raise Exception("chunk too small %s" % len(chunk))

        fft_frames = []
        for i in range(int(config.SYNC_WORD_BITS)):
            chunk_start = i * config.SYMBOL_SIZE
            chunk_end = chunk_start + config.SYMBOL_SIZE
            window = chunk[chunk_start:chunk_end]
            result = numpy.fft.rfft(window, norm="ortho")
            freq_0 = (config.SYMBOL_SIZE * config.FREQ_0) / config.RATE
            freq_1 = (config.SYMBOL_SIZE * config.FREQ_1) / config.RATE
            amp0 = abs(result[freq_0])
            amp1 = abs(result[freq_1])
            fft_frames.append((amp0, amp1))

        bits = [0 if amp0 > amp1 else 1
                for amp0, amp1 in fft_frames]

        # TODO: signal to noise
        # snr = calculate_signal_to_noise(fft_frames)

        decoded_string = codec.bits_to_string(bits)

        if decoded_string == config.SYNC_WORD:

            return 0, start

    return 0.0, None


def read_thread(state,  # type: State
                ):
    stream = open_stream()
    while state.running:
        data = stream.read(int(config.BUFFER_SIZE))
        state.ring.append(data)


def main():

    min_num_of_chunks = int(config.SYNC_WORD_SIZE / config.BUFFER_SIZE) + 1
    num_of_chunks = int(config.SYNC_WORD_SIZE / config.BUFFER_SIZE) + 2
    print("num_of_chunks: %s" % num_of_chunks)

    state = State(None)

    thread = threading.Thread(target=read_thread, args=(state,))
    thread.start()

    try:
        while True:

            # wait until we have enough data
            if len(state.ring) >= min_num_of_chunks:
                snapshot = list(state.ring)
                snapshot = [codec.decode16(s) for s in snapshot]
                snapshot = flatten(snapshot)
                with timed("detect[%s] (%s)" % (len(state.ring), config.BUFFER_SIZE)):
                    snr, sync_word_offset = detect_sync_word(snapshot, scan_count=80)
                    snr = "%.4f" % float(snr)
                    if sync_word_offset is not None:
                        print(snr, sync_word_offset)
                state.ring.popleft()

            time.sleep(0.01)

    except:
        traceback.print_exc()

    finally:
        state.running = False
        thread.join()


main()
