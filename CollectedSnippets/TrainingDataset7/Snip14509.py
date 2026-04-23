def handle_entityref(self, name):
        self.fed.append("&%s;" % name)