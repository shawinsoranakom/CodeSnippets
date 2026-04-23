def test_user(self):
        # For code coverage of the user parameter.  We don't care if we get a
        # permission error from it depending on the test execution environment,
        # that still indicates that it was called.

        uid = os.geteuid()
        test_users = [65534 if uid != 65534 else 65533, uid]
        name_uid = "nobody" if sys.platform != 'darwin' else "unknown"

        if pwd is not None:
            try:
                pwd.getpwnam(name_uid)
                test_users.append(name_uid)
            except KeyError:
                # unknown user name
                name_uid = None

        for user in test_users:
            # posix_spawn() may be used with close_fds=False
            for close_fds in (False, True):
                with self.subTest(user=user, close_fds=close_fds):
                    try:
                        output = subprocess.check_output(
                                [sys.executable, "-c",
                                 "import os; print(os.getuid())"],
                                user=user,
                                close_fds=close_fds)
                    except PermissionError as e:  # (EACCES, EPERM)
                        if e.errno == errno.EACCES:
                            self.assertEqual(e.filename, sys.executable)
                        else:
                            self.assertIsNone(e.filename)
                    else:
                        if isinstance(user, str):
                            user_uid = pwd.getpwnam(user).pw_uid
                        else:
                            user_uid = user
                        child_user = int(output)
                        self.assertEqual(child_user, user_uid)

        with self.assertRaises(ValueError):
            subprocess.check_call(ZERO_RETURN_CMD, user=-1)

        with self.assertRaises(OverflowError):
            subprocess.check_call(ZERO_RETURN_CMD,
                                  cwd=os.curdir, env=os.environ, user=2**64)

        if pwd is None and name_uid is not None:
            with self.assertRaises(ValueError):
                subprocess.check_call(ZERO_RETURN_CMD, user=name_uid)