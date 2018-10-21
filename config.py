# RATE = 41000 / 2
RATE = 44100 * 4

# RATE = 44100
# RATE = 20500
# SYMBOL_SIZE = int(RATE * 0.1)
SYMBOL_SIZE = int(RATE / 500.0)
FREQ_0 = int(SYMBOL_SIZE * 10)
FREQ_1 = int(SYMBOL_SIZE * 15)
SYNC_WORD = "XYZ"
SYNC_WORD_BITS = len(SYNC_WORD) * 8
SYNC_WORD_SIZE = SYNC_WORD_BITS * SYMBOL_SIZE
BUFFER_SIZE = 1024 * 8
FRAME_DATA = "Hello World"
FRAME_SIZE = len(FRAME_DATA) * 8