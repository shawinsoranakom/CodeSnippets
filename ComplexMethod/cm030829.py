def test_framing_large_objects(self):
        if self.py_version < (3, 4):
            self.skipTest('not supported in Python < 3.4')
        N = 1024 * 1024
        small_items = [[i] for i in range(10)]
        obj = [b'x' * N, *small_items, b'y' * N, 'z' * N]
        for proto in range(4, pickle.HIGHEST_PROTOCOL + 1):
            for fast in [False, True]:
                with self.subTest(proto=proto, fast=fast):
                    if not fast:
                        # fast=False by default.
                        # This covers in-memory pickling with pickle.dumps().
                        pickled = self.dumps(obj, proto)
                    else:
                        # Pickler is required when fast=True.
                        if not hasattr(self, 'pickler'):
                            continue
                        buf = io.BytesIO()
                        pickler = self.pickler(buf, protocol=proto)
                        pickler.fast = fast
                        pickler.dump(obj)
                        pickled = buf.getvalue()
                    unpickled = self.loads(pickled)
                    # More informative error message in case of failure.
                    self.assertEqual([len(x) for x in obj],
                                     [len(x) for x in unpickled])
                    # Perform full equality check if the lengths match.
                    self.assertEqual(obj, unpickled)
                    if self.py_version >= (3, 7):
                        n_frames = count_opcode(pickle.FRAME, pickled)
                        # A single frame for small objects between
                        # first two large objects.
                        self.assertEqual(n_frames, 1)
                        self.check_frame_opcodes(pickled)