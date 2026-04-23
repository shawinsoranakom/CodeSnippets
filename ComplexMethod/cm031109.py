def testIteration(self):
        # Test the complex interaction when mixing file-iteration and the
        # various read* methods.
        dataoffset = 16384
        filler = b"ham\n"
        assert not dataoffset % len(filler), \
            "dataoffset must be multiple of len(filler)"
        nchunks = dataoffset // len(filler)
        testlines = [
            b"spam, spam and eggs\n",
            b"eggs, spam, ham and spam\n",
            b"saussages, spam, spam and eggs\n",
            b"spam, ham, spam and eggs\n",
            b"spam, spam, spam, spam, spam, ham, spam\n",
            b"wonderful spaaaaaam.\n"
        ]
        methods = [("readline", ()), ("read", ()), ("readlines", ()),
                   ("readinto", (array("b", b" "*100),))]

        # Prepare the testfile
        bag = self.open(TESTFN, "wb")
        bag.write(filler * nchunks)
        bag.writelines(testlines)
        bag.close()
        # Test for appropriate errors mixing read* and iteration
        for methodname, args in methods:
            f = self.open(TESTFN, 'rb')
            self.assertEqual(next(f), filler)
            meth = getattr(f, methodname)
            meth(*args)  # This simply shouldn't fail
            f.close()

        # Test to see if harmless (by accident) mixing of read* and
        # iteration still works. This depends on the size of the internal
        # iteration buffer (currently 8192,) but we can test it in a
        # flexible manner.  Each line in the bag o' ham is 4 bytes
        # ("h", "a", "m", "\n"), so 4096 lines of that should get us
        # exactly on the buffer boundary for any power-of-2 buffersize
        # between 4 and 16384 (inclusive).
        f = self.open(TESTFN, 'rb')
        for i in range(nchunks):
            next(f)
        testline = testlines.pop(0)
        try:
            line = f.readline()
        except ValueError:
            self.fail("readline() after next() with supposedly empty "
                        "iteration-buffer failed anyway")
        if line != testline:
            self.fail("readline() after next() with empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))
        testline = testlines.pop(0)
        buf = array("b", b"\x00" * len(testline))
        try:
            f.readinto(buf)
        except ValueError:
            self.fail("readinto() after next() with supposedly empty "
                        "iteration-buffer failed anyway")
        line = buf.tobytes()
        if line != testline:
            self.fail("readinto() after next() with empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))

        testline = testlines.pop(0)
        try:
            line = f.read(len(testline))
        except ValueError:
            self.fail("read() after next() with supposedly empty "
                        "iteration-buffer failed anyway")
        if line != testline:
            self.fail("read() after next() with empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))
        try:
            lines = f.readlines()
        except ValueError:
            self.fail("readlines() after next() with supposedly empty "
                        "iteration-buffer failed anyway")
        if lines != testlines:
            self.fail("readlines() after next() with empty buffer "
                        "failed. Got %r, expected %r" % (line, testline))
        f.close()

        # Reading after iteration hit EOF shouldn't hurt either
        f = self.open(TESTFN, 'rb')
        try:
            for line in f:
                pass
            try:
                f.readline()
                f.readinto(buf)
                f.read()
                f.readlines()
            except ValueError:
                self.fail("read* failed after next() consumed file")
        finally:
            f.close()