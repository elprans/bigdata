import time
import threading


class avg_rec_rate(object):
    def __init__(self):
        self.count = 0
        self.stats = []
        self.mutex = threading.Lock()
        self.worker = threading.Thread(target=self._maintain)
        self.worker.daemon = True
        self.worker.start()
        self._report = None

    def _maintain(self):
        while True:
            time.sleep(5)
            if len(self.stats) < 500:
                continue

            with self.mutex:
                count = self.count
                stats = self.stats[0:-1]
                self.stats = self.stats[:]
            count_delta = stats[-1][0] - stats[0][0]
            time_delta = stats[-1][1] - stats[0][1]
            rate = count_delta / time_delta
            timestamp = stats[-1][1]
            print(
                "%s Total count: %d %.2f recs/sec " %
                (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
                 count, rate))

    def tag(self, count=1):
        with self.mutex:
            self.count += count
            self.stats.append((self.count, time.time()))

