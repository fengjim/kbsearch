import threading
import sys

class LogThreadWorker(threading.Thread):
    def __init__(self, log_file):
        threading.Thread.__init__(self)
        self._log_file = log_file
        self._kb_buffer = []
        self._buffer_lock = threading.Lock()
        self._is_running = False
        self._counter = 0

    def log(self, kb):
        self._buffer_lock.acquire()
        self._kb_buffer.append(kb)
        self._buffer_lock.release()

    def run(self):
        self._is_running = True
        filehandler = None
        try:
            if self._log_file:
                # make sure the output is flushed into the file immediately
                filehandler = open(self._log_file, 'a', 0)
            else:
                filehandler = sys.stdout
            while self._is_running or self._kb_buffer:
                kb = None

                if self._kb_buffer:
                    self._buffer_lock.acquire()
                    kb = self._kb_buffer.pop(0)
                    self._buffer_lock.release()

                if kb:
                    filehandler.write(kb + '\n')
                    self._counter += 1
        except Exception as ex:
            print('error:', str(ex))
        finally:
            if self._log_file:
                filehandler.close()
    def stop(self):
        self._is_running = False

    def num_of_kbs(self):
        return self._counter
