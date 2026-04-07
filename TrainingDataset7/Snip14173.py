def client(self):
        return pywatchman.client(timeout=self.client_timeout)