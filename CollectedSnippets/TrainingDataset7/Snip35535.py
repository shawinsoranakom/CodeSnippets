def notify(self, id_):
        if id_ == "error":
            raise ForcedError()
        self.notified.append(id_)