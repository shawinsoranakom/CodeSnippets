def send(self, data):
        """Send 'data' to the server.
        ``data`` can be a string object, a bytes object, an array object, a
        file-like object that supports a .read() method, or an iterable object.
        """

        if self.sock is None:
            if self.auto_open:
                self.connect()
            else:
                raise NotConnected()

        if self.debuglevel > 0:
            print("send:", repr(data))
        if hasattr(data, "read") :
            if self.debuglevel > 0:
                print("sending a readable")
            encode = self._is_textIO(data)
            if encode and self.debuglevel > 0:
                print("encoding file using iso-8859-1")
            while datablock := data.read(self.blocksize):
                if encode:
                    datablock = datablock.encode("iso-8859-1")
                sys.audit("http.client.send", self, datablock)
                self.sock.sendall(datablock)
            return
        sys.audit("http.client.send", self, data)
        try:
            self.sock.sendall(data)
        except TypeError:
            if isinstance(data, collections.abc.Iterable):
                for d in data:
                    self.sock.sendall(d)
            else:
                raise TypeError("data should be a bytes-like object "
                                "or an iterable, got %r" % type(data))