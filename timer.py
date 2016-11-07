import threading
import config

# Timer thread
#class TimerThread(threading.Thread):
class TimerThread:

    def __init__(self, timeout_handler):
        #threading.Thread.__init__(self)
        self.event = threading.Event()
        self.timeout_handler = timeout_handler
        self.started = False
        self.exit = False
        threading.Thread(target=self.run).start()

    def run(self):
        while True:
            # Exit thread
            if self.exit:
                return

            # if the timer is started 
            if self.started:
                if not self.event.wait(config.TIMEOUT_MSEC * (0.001)):
                    # if we returned from a wait from timout
                    self.timeout_handler()
            else: pass

    def stop(self):
        self.started = False
        self.event.set()

    def start(self):
        self.started = True
        self.event.clear()

    def exit(self):
        self.exit = True