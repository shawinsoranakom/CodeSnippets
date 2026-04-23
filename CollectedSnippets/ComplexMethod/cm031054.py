def test_copy_error_handling(self):
        def make_raiser(err):
            def raiser(*args, **kwargs):
                raise OSError(err, os.strerror(err))
            return raiser

        base = self.cls(self.base)
        source = base / 'fileA'
        target = base / 'copyA'

        # Raise non-fatal OSError from all available fast copy functions.
        with contextlib.ExitStack() as ctx:
            if fcntl and hasattr(fcntl, 'FICLONE'):
                ctx.enter_context(mock.patch('fcntl.ioctl', make_raiser(errno.EXDEV)))
            if posix and hasattr(posix, '_fcopyfile'):
                ctx.enter_context(mock.patch('posix._fcopyfile', make_raiser(errno.ENOTSUP)))
            if hasattr(os, 'copy_file_range'):
                ctx.enter_context(mock.patch('os.copy_file_range', make_raiser(errno.EXDEV)))
            if hasattr(os, 'sendfile'):
                ctx.enter_context(mock.patch('os.sendfile', make_raiser(errno.ENOTSOCK)))

            source.copy(target)
            self.assertTrue(target.exists())
            self.assertEqual(source.read_text(), target.read_text())

        # Raise fatal OSError from first available fast copy function.
        if fcntl and hasattr(fcntl, 'FICLONE'):
            patchpoint = 'fcntl.ioctl'
        elif posix and hasattr(posix, '_fcopyfile'):
            patchpoint = 'posix._fcopyfile'
        elif hasattr(os, 'copy_file_range'):
            patchpoint = 'os.copy_file_range'
        elif hasattr(os, 'sendfile'):
            patchpoint = 'os.sendfile'
        else:
            return
        with mock.patch(patchpoint, make_raiser(errno.ENOENT)):
            self.assertRaises(FileNotFoundError, source.copy, target)