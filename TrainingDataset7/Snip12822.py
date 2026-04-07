def is_hidden(self):
        return all(w.is_hidden for w in self.widgets)