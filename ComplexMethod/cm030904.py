def test_group(self):
        gid = os.getegid()
        group_list = [65534 if gid != 65534 else 65533]
        name_group = _get_test_grp_name()

        if grp is not None:
            group_list.append(name_group)

        for group in group_list + [gid]:
            # posix_spawn() may be used with close_fds=False
            for close_fds in (False, True):
                with self.subTest(group=group, close_fds=close_fds):
                    try:
                        output = subprocess.check_output(
                                [sys.executable, "-c",
                                 "import os; print(os.getgid())"],
                                group=group,
                                close_fds=close_fds)
                    except PermissionError as e:  # (EACCES, EPERM)
                        self.assertIsNone(e.filename)
                    else:
                        if isinstance(group, str):
                            group_gid = grp.getgrnam(group).gr_gid
                        else:
                            group_gid = group

                        child_group = int(output)
                        self.assertEqual(child_group, group_gid)

        # make sure we bomb on negative values
        with self.assertRaises(ValueError):
            subprocess.check_call(ZERO_RETURN_CMD, group=-1)

        with self.assertRaises(OverflowError):
            subprocess.check_call(ZERO_RETURN_CMD,
                                  cwd=os.curdir, env=os.environ, group=2**64)

        if grp is None:
            with self.assertRaises(ValueError):
                subprocess.check_call(ZERO_RETURN_CMD, group=name_group)