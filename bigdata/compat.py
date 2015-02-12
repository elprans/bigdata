import sys
py3k = sys.version_info >= (3, 0)

if py3k:
    import queue
else:
    import Queue as queue
