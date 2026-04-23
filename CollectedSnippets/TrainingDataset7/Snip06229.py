def encode(self, password, salt, n=None, r=None, p=None):
        self._check_encode_args(password, salt)
        n = n or self.work_factor
        r = r or self.block_size
        p = p or self.parallelism
        hash_ = hashlib.scrypt(
            password=force_bytes(password),
            salt=force_bytes(salt),
            n=n,
            r=r,
            p=p,
            maxmem=self.maxmem,
            dklen=64,
        )
        hash_ = base64.b64encode(hash_).decode("ascii").strip()
        return "%s$%d$%s$%d$%d$%s" % (self.algorithm, n, force_str(salt), r, p, hash_)