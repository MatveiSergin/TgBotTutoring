import time

queue = [(1, time.time() + 10)]
time.sleep(8)
queue.append((2, time.time() + 10))

