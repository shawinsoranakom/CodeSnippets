def test_libc_ver(self):
        if support.is_emscripten:
            assert platform.libc_ver() == ("emscripten", "4.0.12")
            return
        # check that libc_ver(executable) doesn't raise an exception
        if os.path.isdir(sys.executable) and \
           os.path.exists(sys.executable+'.exe'):
            # Cygwin horror
            executable = sys.executable + '.exe'
        elif sys.platform == "win32" and not os.path.exists(sys.executable):
            # App symlink appears to not exist, but we want the
            # real executable here anyway
            import _winapi
            executable = _winapi.GetModuleFileName(0)
        else:
            executable = sys.executable
        platform.libc_ver(executable)

        filename = os_helper.TESTFN
        self.addCleanup(os_helper.unlink, filename)

        with mock.patch('os.confstr', create=True, return_value='mock 1.0'):
            # test os.confstr() code path
            self.assertEqual(platform.libc_ver(), ('mock', '1.0'))

            # test the different regular expressions
            for data, expected in (
                (b'__libc_init', ('libc', '')),
                (b'GLIBC_2.9', ('glibc', '2.9')),
                (b'libc.so.1.2.5', ('libc', '1.2.5')),
                (b'libc_pthread.so.1.2.5', ('libc', '1.2.5_pthread')),
                (b'/aports/main/musl/src/musl-1.2.5', ('musl', '1.2.5')),
                # musl uses semver, but we accept some variations anyway:
                (b'/aports/main/musl/src/musl-12.5', ('musl', '12.5')),
                (b'/aports/main/musl/src/musl-1.2.5.7', ('musl', '1.2.5.7')),
                (b'libc.musl.so.1', ('musl', '1')),
                (b'libc.musl-x86_64.so.1.2.5', ('musl', '1.2.5')),
                (b'ld-musl.so.1', ('musl', '1')),
                (b'ld-musl-x86_64.so.1.2.5', ('musl', '1.2.5')),
                (b'', ('', '')),
            ):
                with open(filename, 'wb') as fp:
                    fp.write(b'[xxx%sxxx]' % data)
                    fp.flush()

                # os.confstr() must not be used if executable is set
                self.assertEqual(platform.libc_ver(executable=filename),
                                 expected)

        # binary containing multiple versions: get the most recent,
        # make sure that eg 1.9 is seen as older than 1.23.4, and that
        # the arguments don't count even if they are set.
        chunksize = 200
        for data, expected in (
                (b'GLIBC_1.23.4\0GLIBC_1.9\0GLIBC_1.21\0', ('glibc', '1.23.4')),
                (b'libc.so.2.4\0libc.so.9\0libc.so.23.1\0', ('libc', '23.1')),
                (b'musl-1.4.1\0musl-2.1.1\0musl-2.0.1\0', ('musl', '2.1.1')),
                (
                    b'libc.musl-x86_64.so.1.4.1\0libc.musl-x86_64.so.2.1.1\0libc.musl-x86_64.so.2.0.1',
                    ('musl', '2.1.1'),
                ),
                (
                    b'ld-musl-x86_64.so.1.4.1\0ld-musl-x86_64.so.2.1.1\0ld-musl-x86_64.so.2.0.1',
                    ('musl', '2.1.1'),
                ),
                (b'no match here, so defaults are used', ('test', '100.1.0')),
            ):
            with open(filename, 'wb') as f:
                # test match at chunk boundary
                f.write(b'x'*(chunksize - 10))
                f.write(data)
            self.assertEqual(
                expected,
                platform.libc_ver(
                    filename,
                    lib='test',
                    version='100.1.0',
                    chunksize=chunksize,
                    ),
                )