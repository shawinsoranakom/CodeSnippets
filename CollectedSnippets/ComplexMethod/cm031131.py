def setUp(self):
        # Set of characters (as byte integers) that don't need to be encoded
        # in headers.
        self.hlit = list(chain(
            range(ord('a'), ord('z') + 1),
            range(ord('A'), ord('Z') + 1),
            range(ord('0'), ord('9') + 1),
            (c for c in b'!*+-/')))
        # Set of characters (as byte integers) that do need to be encoded in
        # headers.
        self.hnon = [c for c in range(256) if c not in self.hlit]
        assert len(self.hlit) + len(self.hnon) == 256
        # Set of characters (as byte integers) that don't need to be encoded
        # in bodies.
        self.blit = list(range(ord(' '), ord('~') + 1))
        self.blit.append(ord('\t'))
        self.blit.remove(ord('='))
        # Set of characters (as byte integers) that do need to be encoded in
        # bodies.
        self.bnon = [c for c in range(256) if c not in self.blit]
        assert len(self.blit) + len(self.bnon) == 256