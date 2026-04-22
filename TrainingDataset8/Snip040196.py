def tearDown(self):
        super(PollingPathWatcherTest, self).tearDown()
        self.util_patch.stop()
        self.executor_patch.stop()
        self.sleep_patch.stop()