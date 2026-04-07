def setUp(self):
        signals.setting_changed.connect(self.receiver)
        self.addCleanup(signals.setting_changed.disconnect, self.receiver)
        # Create a spy that's connected to the `setting_changed` signal and
        # executed AFTER `self.receiver`.
        self.spy_receiver = mock.Mock()
        signals.setting_changed.connect(self.spy_receiver)
        self.addCleanup(signals.setting_changed.disconnect, self.spy_receiver)