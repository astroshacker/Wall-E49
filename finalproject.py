from machine import Pin, I2C, ENC, Timer, ADC, PWM
from board import A10, ADC6
from board import A10, A5, A8, A6, A20, A21, SDA, SCL
from time import sleep
import time
from network import WLAN, STA_IF, mDNS
from mpu9250 import MPU9250
from plotclient import PlotClient
from mqttclient import MQTTClient

#Connect to WiFi
wlan = WLAN(STA_IF)
wlan.active(True)

wlan.connect('2WIRE030', '3922451880', 5000)

while not wlan.isconnected():
    print("Waiting for wlan connection")
    sleep(1)

print("WiFi connected at", wlan.ifconfig()[0])

# Advertise as 'hostname', alternative to IP address
try:
    hostname = 'veryviruswifi'
    mdns = mDNS(wlan)
    mdns.start(hostname, "MicroPython REPL")
    mdns.addService('_repl', '_tcp', 23, hostname)
    print("Advertised locally as {}.local".format(hostname))
except OSError:
    print("Failed starting mDNS server - already started?")

# start telnet server for remote login
from network import telnet

print("start telnet server")
telnet.start(user='veryviruswifi', password='1111')

# fetch NTP time
from machine import RTC

print("inquire RTC time")
rtc = RTC()
rtc.ntp_sync(server="pool.ntp.org")

timeout = 10
for _ in range(timeout):
    if rtc.synced():
        break
    print("Waiting for rtc time")
    sleep(1)

if rtc.synced():
    print(time.strftime("%c", time.localtime()))
else:
    print("could not get NTP time")

#Connect to broker
BROKER = "mqtt.thingspeak.com"
USER = None
PWD = None

print("Connecting to broker", BROKER, "...")
mqtt = MQTTClient(BROKER, user = None, password = None, ssl = True)
print("Connected!")

MPU9250._chip_id = 115
i2c = I2C(id=0, scl=Pin(SCL), sda=Pin(SDA), freq = 100000)

#Detect all devices connected to I2C bus
print("scanning I2C bus ...")
print("I2C:", i2c.scan())

#Initialize MPU
imu = MPU9250(i2c)

#Initialize IR Sensor
adc6 = ADC(Pin(ADC6))
adc6.atten(ADC.ATTN_11DB)

enc2 = ENC(0, Pin(A6))
enc2.filter(1023)
print("Encoder:", enc2)

pwm1 = PWM(A8, freq = 20, duty = 100)
pwm2 = PWM(A5, freq = 20, duty = 100)

pwm3 = PWM(A20, freq = 20, duty = 100)
pwm4 = PWM(A21, freq = 20, duty = 100)

max_code = 0

def turn(timer):
    enc2.clear()
    
    while enc2.count() < (87*2):
        global max_index
        global max_code
        print(enc2.count())
        
        pwm1.duty(100)
        pwm2.duty(100)
        pwm3.duty(100)
        pwm4.duty(60)

        next_value = adc6.read()

        if max_code <= next_value:
            max_code = next_value
            max_index = enc2.count()

        print('best dist: ' + str(max_code))
        print('best index: ' + str(max_index))

    sleep(1)
    turntwo(max_index, max_code)

def turntwo(max_dist_index, max_code_value):
    enc2.clear()
    enc2.resume()
    while enc2.count() < max_index:
        print('turn2count: ' + str(enc2.count()))
        pwm1.duty(100)
        pwm2.duty(100)
        pwm3.duty(100)
        pwm4.duty(60)

    pwm1.duty(100)
    pwm2.duty(100)
    pwm3.duty(100)
    pwm4.duty(100)

    sleep(1)
    gostraight(max_code_value)

def gostraight(max_code_value):
    #distance traveled per slot = diameter of wheel = 2pi(2.5/2) / 20 slots = .4 in
    counts_travel = int((-.0000002 * (float(max_code))**2 + .0036*(float(max_code)) + 2.41+2) / .4)
    print('counts_travel: ' + str(counts_travel))

    enc2.clear()
    enc2.resume()
    while enc2.count() < counts_travel:
        print('straight: ' + str(enc2.count()))
        pwm1.duty(100)
        pwm2.duty(60)
        pwm3.duty(100)
        pwm4.duty(60)

    temperature = imu.temperature
    print('temperature: '+ str(temperature))
    topic = "channels/" + "436089" + "/publish/" + "S2L5BJH71OCHNBLN"
    message = "field1={}".format(temperature)

    print("PUBLISH topic = {} message = {}".format(topic, message))
    mqtt.publish(topic, message)

    pwm1.duty(100)
    pwm2.duty(100)
    pwm3.duty(100)
    pwm4.duty(100)

tm = Timer(1)
tm.init(period=7000, mode=tm.PERIODIC, callback=turn)
