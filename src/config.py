RATE = 44100
SYMBOL_SIZE = 49
FREQ_1, FREQ_0 = 14700, 11025
SYNC_WORD = "A"
SYNC_WORD_BITS = len(SYNC_WORD) * 8
SYNC_WORD_SIZE = SYNC_WORD_BITS * SYMBOL_SIZE
FRAME_DATA = "123456789 " * 10
FRAME_SIZE = len(FRAME_DATA) * 8
SKIP_SAMPLES = 7
BUFFER_SIZE = SYMBOL_SIZE * 2
BAND_WIDTH = 20
SNR_MIN = 5
