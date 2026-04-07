def add(self, level, message, extra_tags=""):
        self.store.append(Message(level, message, extra_tags))