def setUp(self):
        self.signals = []
        self.signaled_environ = None
        request_started.connect(self.register_started)
        self.addCleanup(request_started.disconnect, self.register_started)
        request_finished.connect(self.register_finished)
        self.addCleanup(request_finished.disconnect, self.register_finished)