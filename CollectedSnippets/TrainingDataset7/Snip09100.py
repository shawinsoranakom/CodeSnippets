def signature(self, value, key=None):
        key = key or self.key
        return base64_hmac(self.salt + "signer", value, key, algorithm=self.algorithm)