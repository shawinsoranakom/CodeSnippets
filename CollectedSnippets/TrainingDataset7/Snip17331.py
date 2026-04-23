def setUp(self):
        request_started.disconnect(close_old_connections)
        self.addCleanup(request_started.connect, close_old_connections)