def stop(self):
        self.client.close()
        super().stop()