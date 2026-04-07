def handle_charref(self, name):
        self.fed.append("&#%s;" % name)