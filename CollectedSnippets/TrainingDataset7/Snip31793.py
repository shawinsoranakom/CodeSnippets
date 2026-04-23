def sendall(self, data):
        self.makefile("wb").write(data)