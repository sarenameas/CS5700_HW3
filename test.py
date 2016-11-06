from threading import Timer
import time

def again():
    print("again")

def hello():
    print("hello, world")
    t = Timer(1, again)
    t.start()  # after 30 seconds, "hello, world" will be printed

t = Timer(0.1, hello)
t.start()  # after 30 seconds, "hello, world" will be printed

print("is this blocked?")
time.sleep(3)

if t:
    t.cancel()
    print("can cancel already stopped timer!")