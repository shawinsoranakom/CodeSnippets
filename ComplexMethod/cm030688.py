def test_access_parameter(self):
        # Test for "access" keyword parameter
        mapsize = 10
        with open(TESTFN, "wb") as fp:
            fp.write(b"a"*mapsize)
        with open(TESTFN, "rb") as f:
            m = mmap.mmap(f.fileno(), mapsize, access=mmap.ACCESS_READ)
            self.assertEqual(m[:], b'a'*mapsize, "Readonly memory map data incorrect.")

            # Ensuring that readonly mmap can't be slice assigned
            try:
                m[:] = b'b'*mapsize
            except TypeError:
                pass
            else:
                self.fail("Able to write to readonly memory map")

            # Ensuring that readonly mmap can't be item assigned
            try:
                m[0] = b'b'
            except TypeError:
                pass
            else:
                self.fail("Able to write to readonly memory map")

            # Ensuring that readonly mmap can't be write() to
            try:
                m.seek(0, 0)
                m.write(b'abc')
            except TypeError:
                pass
            else:
                self.fail("Able to write to readonly memory map")

            # Ensuring that readonly mmap can't be write_byte() to
            try:
                m.seek(0, 0)
                m.write_byte(b'd')
            except TypeError:
                pass
            else:
                self.fail("Able to write to readonly memory map")

            if hasattr(m, 'resize'):
                # Ensuring that readonly mmap can't be resized
                with self.assertRaises(TypeError):
                    m.resize(2 * mapsize)
            with open(TESTFN, "rb") as fp:
                self.assertEqual(fp.read(), b'a'*mapsize,
                                 "Readonly memory map data file was modified")

        # Opening mmap with size too big
        with open(TESTFN, "r+b") as f:
            try:
                m = mmap.mmap(f.fileno(), mapsize+1)
            except ValueError:
                # we do not expect a ValueError on Windows
                # CAUTION:  This also changes the size of the file on disk, and
                # later tests assume that the length hasn't changed.  We need to
                # repair that.
                if sys.platform.startswith('win'):
                    self.fail("Opening mmap with size+1 should work on Windows.")
            else:
                # we expect a ValueError on Unix, but not on Windows
                if not sys.platform.startswith('win'):
                    self.fail("Opening mmap with size+1 should raise ValueError.")
                m.close()
            if sys.platform.startswith('win'):
                # Repair damage from the resizing test.
                with open(TESTFN, 'r+b') as f:
                    f.truncate(mapsize)

        # Opening mmap with access=ACCESS_WRITE
        with open(TESTFN, "r+b") as f:
            m = mmap.mmap(f.fileno(), mapsize, access=mmap.ACCESS_WRITE)
            # Modifying write-through memory map
            m[:] = b'c'*mapsize
            self.assertEqual(m[:], b'c'*mapsize,
                   "Write-through memory map memory not updated properly.")
            m.flush()
            m.close()
        with open(TESTFN, 'rb') as f:
            stuff = f.read()
        self.assertEqual(stuff, b'c'*mapsize,
               "Write-through memory map data file not updated properly.")

        # Opening mmap with access=ACCESS_COPY
        with open(TESTFN, "r+b") as f:
            m = mmap.mmap(f.fileno(), mapsize, access=mmap.ACCESS_COPY)
            # Modifying copy-on-write memory map
            m[:] = b'd'*mapsize
            self.assertEqual(m[:], b'd' * mapsize,
                             "Copy-on-write memory map data not written correctly.")
            m.flush()
            with open(TESTFN, "rb") as fp:
                self.assertEqual(fp.read(), b'c'*mapsize,
                                 "Copy-on-write test data file should not be modified.")
            if hasattr(m, 'resize'):
                # Ensuring copy-on-write maps cannot be resized
                self.assertRaises(TypeError, m.resize, 2 * mapsize)
            m.close()

        # Ensuring invalid access parameter raises exception
        with open(TESTFN, "r+b") as f:
            self.assertRaises(ValueError, mmap.mmap, f.fileno(), mapsize, access=4)

        if os.name == "posix":
            # Try incompatible flags, prot and access parameters.
            with open(TESTFN, "r+b") as f:
                self.assertRaises(ValueError, mmap.mmap, f.fileno(), mapsize,
                                  flags=mmap.MAP_PRIVATE,
                                  prot=mmap.PROT_READ, access=mmap.ACCESS_WRITE)

            # Try writing with PROT_EXEC and without PROT_WRITE
            prot = mmap.PROT_READ | getattr(mmap, 'PROT_EXEC', 0)
            with open(TESTFN, "r+b") as f:
                try:
                    m = mmap.mmap(f.fileno(), mapsize, prot=prot)
                except PermissionError:
                    # on macOS 14, PROT_READ | PROT_EXEC is not allowed
                    pass
                else:
                    self.assertRaises(TypeError, m.write, b"abcdef")
                    self.assertRaises(TypeError, m.write_byte, 0)
                    m.close()