def get_test_runner_kwargs(self):
        kwargs = {
            "failfast": self.failfast,
            "resultclass": self.get_resultclass(),
            "verbosity": self.verbosity,
            "buffer": self.buffer,
            "durations": self.durations,
        }
        return kwargs