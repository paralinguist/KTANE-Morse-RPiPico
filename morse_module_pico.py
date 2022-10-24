#Libraries from this article here:
#https://www.circuitschools.com/interfacing-16x2-lcd-module-with-raspberry-pi-pico-with-and-without-i2c/
from machine import Pin
from sys import stdin
from machine import Timer
from gpio_lcd import GpioLcd
import select
import time
import random

DISARMED = 0
ARMED = 1

status = DISARMED

up_pin = 15
down_pin = 12
tx_pin = 13
up_button = Pin(up_pin, Pin.IN, Pin.PULL_UP)
down_button = Pin(down_pin, Pin.IN, Pin.PULL_UP)
tx_button = Pin(tx_pin, Pin.IN, Pin.PULL_UP)
led = Pin(14, Pin.OUT)

up_button_last = time.ticks_ms()
down_button_last = time.ticks_ms()
tx_button_last = time.ticks_ms()

counter = 0

#morse constants
DOT = 0.5
DASH = 1.5
INTRA_LETTER = 0.5
INTER_LETTER = 1.5
INTER_WORD = 3.5

MORSE = {'A':'.-', 'B':'-...',
                    'C':'-.-.', 'D':'-..', 'E':'.',
                    'F':'..-.', 'G':'--.', 'H':'....',
                    'I':'..', 'J':'.---', 'K':'-.-',
                    'L':'.-..', 'M':'--', 'N':'-.',
                    'O':'---', 'P':'.--.', 'Q':'--.-',
                    'R':'.-.', 'S':'...', 'T':'-',
                    'U':'..-', 'V':'...-', 'W':'.--',
                    'X':'-..-', 'Y':'-.--', 'Z':'--..',
                    '1':'.----', '2':'..---', '3':'...--',
                    '4':'....-', '5':'.....', '6':'-....',
                    '7':'--...', '8':'---..', '9':'----.',
                    '0':'-----', ', ':'--..--', '.':'.-.-.-',
                    '?':'..--..', '/':'-..-.', '-':'-....-',
                    '(':'-.--.', ')':'-.--.-'}
                    
WORD_LIST = {"3.505":"SHELL","3.515":"HALLS", "3.522":"SLICK","3.532":"TRICK","3.535":"BOXES",
                "3.542":"LEAKS","3.545":"STROBE","3.552":"BISTRO","3.555":"FLICK",
                "3.565":"BOMBS","3.572":"BREAK","3.575":"BRICK","3.582":"STEAK",
                "3.592":"STING","3.595":"VECTOR","3.600":"BEATS"}
FREQUENCIES = list(WORD_LIST.keys())
FREQUENCIES.sort()
display_freq = FREQUENCIES[0]

lcd = GpioLcd(rs_pin=Pin(16),
              enable_pin=Pin(17),
              d4_pin=Pin(18),
              d5_pin=Pin(19),
              d6_pin=Pin(20),
              d7_pin=Pin(21),
              num_lines=2, num_columns=16)

frequency = ""
morse_word = ""

def get_new_word():
  global frequency, morse_word
  frequency, morse_word = random.choice(list(WORD_LIST.items()))

def display_message(message):
  lcd.clear()
  lcd.putstr(message)

def display_disarmed():
  global status
  print('D', end='')
  lcd.clear()
  lcd.move_to(3,0)
  lcd.putstr('DISARMED')
  lcd.move_to(0,1)
  lcd.putstr('HAVE A NICE DAY ')
  happy_face = bytearray([0x00,0x0A,0x00,0x04,0x00,0x11,0x0E,0x00])
  lcd.custom_char(0, happy_face)
  lcd.putchar(chr(0))
  status = DISARMED
  get_new_word()

def button_handler(pin):
  global up_button_last, down_button_last, tx_button_last, counter
  if pin == up_button:
    print("UP")
    if time.ticks_diff(time.ticks_ms(), up_button_last) > 250:
      counter += 1
      if counter >= len(FREQUENCIES):              
        counter = 0
      display_message(FREQUENCIES[counter] + " MHz")
      up_button_last = time.ticks_ms()
  elif pin == tx_button and status == ARMED:
    if time.ticks_diff(time.ticks_ms(), tx_button_last) > 500:
      if WORD_LIST[FREQUENCIES[counter]] == morse_word:
        display_disarmed()
      else:
        lcd.move_to(0,1)
        lcd.putstr('WRONG')
        print('S', end='')
      tx_button_last = time.ticks_ms()
  elif pin == down_button:
    print("DWN")
    if time.ticks_diff(time.ticks_ms(), down_button_last) > 250:
      counter -= 1
      if counter < 0:              
        counter = len(FREQUENCIES) - 1
      display_message(FREQUENCIES[counter] + " MHz")
      down_button_last = time.ticks_ms()

#receives 1s if registered and active, 0s otherwise
def server_checkin():
  global status
  if status == DISARMED:
    print('!', end='')
  poll = select.poll()
  poll.register(stdin, select.POLLIN)
  if poll.poll(0):
    serial_input = stdin.read(1)
    if serial_input == "1" and status == DISARMED:
      status = ARMED
      get_new_word()
      display_message(FREQUENCIES[counter] + " MHz")
    elif serial_input == "0":
      status = DISARMED
  poll.unregister(stdin)

led.value(0)
get_new_word()

up_button.irq(trigger = machine.Pin.IRQ_RISING, handler = button_handler)
down_button.irq(trigger = machine.Pin.IRQ_RISING, handler = button_handler)
tx_button.irq(trigger = machine.Pin.IRQ_RISING, handler = button_handler)
serial_timer = Timer(period=3000, mode=Timer.PERIODIC, callback=lambda t:server_checkin())

#display_message(display_freq + " MHz")

while True:
    if status == ARMED:
      for letter in morse_word:
        for flash in MORSE[letter]:
          led.value(1)
          if flash == ".":
            time.sleep(DOT)
          elif flash == "-":
            time.sleep(DASH)
          led.value(0)
          if status == DISARMED:
            break
          time.sleep(INTRA_LETTER)
        if status == DISARMED:
            break
        time.sleep(INTER_LETTER)
