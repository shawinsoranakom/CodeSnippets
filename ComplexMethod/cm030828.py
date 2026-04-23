def check_frame_opcodes(self, pickled):
        """
        Check the arguments of FRAME opcodes in a protocol 4+ pickle.

        Note that binary objects that are larger than FRAME_SIZE_TARGET are not
        framed by default and are therefore considered a frame by themselves in
        the following consistency check.
        """
        frame_end = frameless_start = None
        frameless_opcodes = {'BINBYTES', 'BINUNICODE', 'BINBYTES8',
                             'BINUNICODE8', 'BYTEARRAY8'}
        for op, arg, pos in pickletools.genops(pickled):
            if frame_end is not None:
                self.assertLessEqual(pos, frame_end)
                if pos == frame_end:
                    frame_end = None

            if frame_end is not None:  # framed
                self.assertNotEqual(op.name, 'FRAME')
                if op.name in frameless_opcodes:
                    # Only short bytes and str objects should be written
                    # in a frame
                    self.assertLessEqual(len(arg), self.FRAME_SIZE_TARGET)

            else:  # not framed
                if (op.name == 'FRAME' or
                    (op.name in frameless_opcodes and
                     len(arg) > self.FRAME_SIZE_TARGET)):
                    # Frame or large bytes or str object
                    if frameless_start is not None:
                        # Only short data should be written outside of a frame
                        self.assertLess(pos - frameless_start,
                                        self.FRAME_SIZE_MIN)
                        frameless_start = None
                elif frameless_start is None and op.name != 'PROTO':
                    frameless_start = pos

            if op.name == 'FRAME':
                self.assertGreaterEqual(arg, self.FRAME_SIZE_MIN)
                frame_end = pos + 9 + arg

        pos = len(pickled)
        if frame_end is not None:
            self.assertEqual(frame_end, pos)
        elif frameless_start is not None:
            self.assertLess(pos - frameless_start, self.FRAME_SIZE_MIN)