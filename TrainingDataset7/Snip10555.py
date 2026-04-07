def feed(self, line):
        self.buff.append(" " * (self.indentation * 4) + line)