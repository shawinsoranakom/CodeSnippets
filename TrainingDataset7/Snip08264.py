def _write_content(self, file, timeout, value):
        expiry = self.get_backend_timeout(timeout)
        file.write(pickle.dumps(expiry, self.pickle_protocol))
        file.write(zlib.compress(pickle.dumps(value, self.pickle_protocol)))