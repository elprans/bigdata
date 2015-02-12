import time
import threading


class avg_rec_rate(object):
    def __init__(self):
        self.count = 0
        self.mutex = threading.Lock()
        self.worker = threading.Thread(target=self._maintain)
        self.worker.daemon = True
        self.worker.start()
        self._report = None

    def _maintain(self):
        last_time = time.time()
        last_count = 0
        while True:
            time.sleep(5)

            with self.mutex:
                count = self.count

            now = time.time()
            count_delta = count - last_count
            time_delta = now - last_time
            rate = count_delta / time_delta
            start_timestamp = last_time
            end_timestamp = now

            last_time = now
            last_count = count

            print(
                "%s - %s Total count: %d %.2f recs/sec " %
                (
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(start_timestamp)),
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.localtime(end_timestamp)),
                    count, rate
                )
            )

    def tag(self, count=1):
        with self.mutex:
            self.count += count

