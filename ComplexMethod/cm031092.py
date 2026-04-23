def test_negative_fd_ebadf(self, fd):
        tests = [(os.stat, fd)]
        if hasattr(os, "statx"):
            tests.append((os.statx, fd, 0))
        if os.chdir in os.supports_fd:
            tests.append((os.chdir, fd))
        if os.chmod in os.supports_fd:
            tests.append((os.chmod, fd, 0o777))
        if hasattr(os, "chown") and os.chown in os.supports_fd:
            tests.append((os.chown, fd, 0, 0))
        if os.listdir in os.supports_fd:
            tests.append((os.listdir, fd))
        if os.utime in os.supports_fd:
            tests.append((os.utime, fd, (0, 0)))
        if hasattr(os, "truncate") and os.truncate in os.supports_fd:
            tests.append((os.truncate, fd, 0))
        if hasattr(os, 'statvfs') and os.statvfs in os.supports_fd:
            tests.append((os.statvfs, fd))
        if hasattr(os, "setxattr"):
            tests.append((os.getxattr, fd, b"user.test"))
            tests.append((os.setxattr, fd, b"user.test", b"1"))
            tests.append((os.removexattr, fd, b"user.test"))
            tests.append((os.listxattr, fd))
        if os.scandir in os.supports_fd:
            tests.append((os.scandir, fd))

        for func, *args in tests:
            with self.subTest(func=func, args=args):
                with self.assertRaises(OSError) as ctx:
                    func(*args)
                self.assertEqual(ctx.exception.errno, errno.EBADF)

        if (hasattr(os, "execve") and os.execve in os.supports_fd
            and support.has_subprocess_support):
            # glibc fails with EINVAL, musl fails with EBADF
            with self.assertRaises(OSError) as ctx:
                os.execve(fd, [sys.executable, "-c", "pass"], os.environ)
            self.assertIn(ctx.exception.errno, (errno.EBADF, errno.EINVAL))

        if support.MS_WINDOWS:
            import nt
            self.assertFalse(nt._path_exists(fd))
            self.assertFalse(nt._path_lexists(fd))
            self.assertFalse(nt._path_isdir(fd))
            self.assertFalse(nt._path_isfile(fd))
            self.assertFalse(nt._path_islink(fd))
            self.assertFalse(nt._path_isjunction(fd))