def setUp(self):
        self.testvalue = None
        signals.setting_changed.connect(self.signal_callback)
        self.addCleanup(signals.setting_changed.disconnect, self.signal_callback)