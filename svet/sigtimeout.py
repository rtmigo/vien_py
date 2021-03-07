import signal


class TimeLimitedTimeout(Exception):
    pass


class TimeLimited:
    #  based on https://stackoverflow.com/a/49567288
    def __init__(self, seconds: int, error_message: str = None):
        if error_message is None:
            error_message = 'Timed out after {}s.'.format(seconds)
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeLimitedTimeout(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
