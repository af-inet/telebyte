#!/usr/bin/env pythonw
import matplotlib.pyplot as p
import send, config

signal_0 = send.make_signal(config.FREQ_0, config.RATE, config.SYMBOL_SIZE)
signal_1 = send.make_signal(config.FREQ_1, config.RATE, config.SYMBOL_SIZE)

s = p.subplot(211)
s.plot(signal_0)

s = p.subplot(212)
s.plot(signal_1)

p.show()
