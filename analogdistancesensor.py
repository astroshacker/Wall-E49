#https://github.com/bboser/IoT49/blob/master/doc/analog_io.md

from machine import Pin, ADC, Timer
from board import ADC6
from time import sleep

adc6 = ADC(Pin(ADC6))

#set full-scale range
adc6.atten(ADC.ATTN_11DB)

def info(timer):
    #code = 4095 * (Vin/Vref)
    max_code = adc6.read()
    print('code: ' + str(max_code))
    counts_travel = int((-.0000002 * (float(max_code))**2 + .0036*(float(max_code)) + 2.41) / .4)
    print('counts_travel: ' + str(counts_travel))
    

#display distance

tm = Timer(1)
tm.init(period=500, mode=tm.PERIODIC, callback=info)

