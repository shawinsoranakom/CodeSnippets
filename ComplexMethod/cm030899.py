def test_realpath_limit_attack(self):
        # (CVE-2025-4517)

        with ArchiveMaker() as arc:
            # populate the symlinks and dirs that expand in os.path.realpath()
            # The component length is chosen so that in common cases, the unexpanded
            # path fits in PATH_MAX, but it overflows when the final symlink
            # is expanded
            steps = "abcdefghijklmnop"
            if sys.platform == 'win32':
                component = 'd' * 25
            elif 'PC_PATH_MAX' in os.pathconf_names:
                max_path_len = os.pathconf(self.outerdir.parent, "PC_PATH_MAX")
                path_sep_len = 1
                dest_len = len(str(self.destdir)) + path_sep_len
                component_len = (max_path_len - dest_len) // (len(steps) + path_sep_len)
                component = 'd' * component_len
            else:
                raise NotImplementedError("Need to guess component length for {sys.platform}")
            path = ""
            step_path = ""
            for i in steps:
                arc.add(os.path.join(path, component), type=tarfile.DIRTYPE,
                        mode='drwxrwxrwx')
                arc.add(os.path.join(path, i), symlink_to=component)
                path = os.path.join(path, component)
                step_path = os.path.join(step_path, i)
            # create the final symlink that exceeds PATH_MAX and simply points
            # to the top dir.
            # this link will never be expanded by
            # os.path.realpath(strict=False), nor anything after it.
            linkpath = os.path.join(*steps, "l"*254)
            parent_segments = [".."] * len(steps)
            arc.add(linkpath, symlink_to=os.path.join(*parent_segments))
            # make a symlink outside to keep the tar command happy
            arc.add("escape", symlink_to=os.path.join(linkpath, ".."))
            # use the symlinks above, that are not checked, to create a hardlink
            # to a file outside of the destination path
            arc.add("flaglink", hardlink_to=os.path.join("escape", "flag"))
            # now that we have the hardlink we can overwrite the file
            arc.add("flaglink", content='overwrite')
            # we can also create new files as well!
            arc.add("escape/newfile", content='new')

        with (self.subTest('fully_trusted'),
              self.check_context(arc.open(), filter='fully_trusted',
                                 check_flag=False)):
            if sys.platform == 'win32':
                self.expect_exception((FileNotFoundError, FileExistsError))
            elif self.raised_exception:
                # Cannot symlink/hardlink: tarfile falls back to getmember()
                self.expect_exception(KeyError)
                # Otherwise, this block should never enter.
            else:
                self.expect_any_tree(component)
                self.expect_file('flaglink', content='overwrite')
                self.expect_file('../newfile', content='new')
                self.expect_file('escape', type=tarfile.SYMTYPE)
                self.expect_file('a', symlink_to=component)

        for filter in 'tar', 'data':
            with self.subTest(filter), self.check_context(arc.open(), filter=filter):
                exc = self.expect_exception((OSError, KeyError))
                if isinstance(exc, OSError):
                    if sys.platform == 'win32':
                        # 3: ERROR_PATH_NOT_FOUND
                        # 5: ERROR_ACCESS_DENIED
                        # 206: ERROR_FILENAME_EXCED_RANGE
                        self.assertIn(exc.winerror, (3, 5, 206))
                    else:
                        self.assertEqual(exc.errno, errno.ENAMETOOLONG)