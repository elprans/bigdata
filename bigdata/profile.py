import time
import threading


class avg_rec_rate(object):
    def __init__(self):
        self.count = 0
        self.mutex = threading.Lock()
        self.worker = threading.Thread(target=self._maintain)
        self.worker.daemon = True
        self.worker.start()

    def _maintain(self):
        last_time = time.time()
        last_count = 0

        metrics = []

        while True:
            time.sleep(1)

            with self.mutex:
                count = self.count

            # don't start measuring too soon.
            if count < 10000:
                continue

            now = time.time()
            count_delta = count - last_count
            time_delta = now - last_time
            rate = count_delta / time_delta
            end_timestamp = now

            last_time = now
            last_count = count

            metrics.append(rate)

            if len(metrics) % 5 == 0:
                # keep just the last 20 seconds of metrics
                metrics[:] = metrics[-20:]
                avg = sum(metrics) / len(metrics)
                print(
                    "%s Total count: %d, current rate %.2f recs/sec, "
                    "avg %.2f recs/sec " %
                    (
                        time.strftime(
                            "%Y-%m-%d %H:%M:%S",
                            time.localtime(end_timestamp)),
                        count, rate, avg
                    )
                )

    def tag(self, count=1):
        with self.mutex:
            self.count += count

