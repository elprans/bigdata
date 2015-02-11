import cProfile
import pstats
import os
import time


class Profiler(object):
    tests = []

    _setup = None
    _setup_once = None
    name = None

    def __init__(self, options):
        self.test = options.test
        self.dburl = options.dburl
        self.runsnake = options.runsnake
        self.profile = options.profile
        self.dump = options.dump
        self.echo = options.echo
        self.stats = []

    @classmethod
    def init(cls, name):
        cls.name = name

    @classmethod
    def profile(cls, fn):
        if cls.name is None:
            raise ValueError(
                "Need to call Profile.init(<suitename>) first.")
        cls.tests.append(fn)
        return fn

    @classmethod
    def setup(cls, fn):
        if cls._setup is not None:
            raise ValueError("setup function already set to %s" % cls._setup)
        cls._setup = staticmethod(fn)
        return fn

    @classmethod
    def setup_once(cls, fn):
        if cls._setup_once is not None:
            raise ValueError(
                "setup_once function already set to %s" % cls._setup_once)
        cls._setup_once = staticmethod(fn)
        return fn

    def run(self):
        if self.test:
            tests = [fn for fn in self.tests if fn.__name__ == self.test]
            if not tests:
                raise ValueError("No such test: %s" % self.test)
        else:
            tests = self.tests

        if self._setup_once:
            print("Running setup once...")
            self._setup_once(self.dburl, self.echo)
        print("Tests to run: %s" % ", ".join([t.__name__ for t in tests]))
        for test in tests:
            self._run_test(test)
            self.stats[-1].report()

    def _run_with_profile(self, fn):
        pr = cProfile.Profile()
        pr.enable()
        try:
            result = fn()
        finally:
            pr.disable()

        stats = pstats.Stats(pr).sort_stats('cumulative')

        self.stats.append(TestResult(self, fn, stats=stats))
        return result

    def _run_with_time(self, fn):
        now = time.time()
        try:
            return fn()
        finally:
            total = time.time() - now
            self.stats.append(TestResult(self, fn, total_time=total))

    def _run_test(self, fn):
        if self._setup:
            self._setup(self.dburl, self.echo)
        if self.profile or self.runsnake or self.dump:
            self._run_with_profile(fn)
        else:
            self._run_with_time(fn)


class TestResult(object):
    def __init__(self, profile, test, stats=None, total_time=None):
        self.profile = profile
        self.test = test
        self.stats = stats
        self.total_time = total_time

    def report(self):
        print(self._summary())
        if self.profile.profile:
            self.report_stats()

    def _summary(self):
        summary = "%s : %s" % (
            self.test.__name__, self.test.__doc__)
        if self.total_time:
            summary += "; total time %f sec" % self.total_time
        if self.stats:
            summary += "; total fn calls %d" % self.stats.total_calls
        return summary

    def report_stats(self):
        if self.profile.runsnake:
            self._runsnake()
        elif self.profile.dump:
            self._dump()

    def _dump(self):
        self.stats.sort_stats('time', 'calls')
        self.stats.print_stats()

    def _runsnake(self):
        filename = "%s.profile" % self.test.__name__
        try:
            self.stats.dump_stats(filename)
            os.system("runsnake %s" % filename)
        finally:
            os.remove(filename)
