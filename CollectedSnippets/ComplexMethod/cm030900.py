def test_modes(self):
        # Test how file modes are extracted
        # (Note that the modes are ignored on platforms without working chmod)
        with ArchiveMaker() as arc:
            arc.add('all_bits', mode='?rwsrwsrwt')
            arc.add('perm_bits', mode='?rwxrwxrwx')
            arc.add('exec_group_other', mode='?rw-rwxrwx')
            arc.add('read_group_only', mode='?---r-----')
            arc.add('no_bits', mode='?---------')
            arc.add('dir/', mode='?---rwsrwt')
            arc.add('dir_all_bits/', mode='?rwsrwsrwt')

        # On some systems, setting the uid, gid, and/or sticky bit is a no-ops.
        # Check which bits we can set, so we can compare tarfile machinery to
        # a simple chmod.
        tmp_filename = os.path.join(TEMPDIR, "tmp.file")
        with open(tmp_filename, 'w'):
            pass
        try:
            new_mode = (os.stat(tmp_filename).st_mode
                        | stat.S_ISVTX | stat.S_ISGID | stat.S_ISUID)
            try:
                os.chmod(tmp_filename, new_mode)
            except OSError as exc:
                if exc.errno == getattr(errno, "EFTYPE", 0):
                    # gh-108948: On FreeBSD, regular users cannot set
                    # the sticky bit.
                    self.skipTest("chmod() failed with EFTYPE: "
                                  "regular users cannot set sticky bit")
                else:
                    raise

            got_mode = os.stat(tmp_filename).st_mode
            _t_file = 't' if (got_mode & stat.S_ISVTX) else 'x'
            _suid_file = 's' if (got_mode & stat.S_ISUID) else 'x'
            _sgid_file = 's' if (got_mode & stat.S_ISGID) else 'x'
        finally:
            os.unlink(tmp_filename)

        os.mkdir(tmp_filename)
        new_mode = (os.stat(tmp_filename).st_mode
                    | stat.S_ISVTX | stat.S_ISGID | stat.S_ISUID)
        os.chmod(tmp_filename, new_mode)
        got_mode = os.stat(tmp_filename).st_mode
        _t_dir = 't' if (got_mode & stat.S_ISVTX) else 'x'
        _suid_dir = 's' if (got_mode & stat.S_ISUID) else 'x'
        _sgid_dir = 's' if (got_mode & stat.S_ISGID) else 'x'
        os.rmdir(tmp_filename)

        with self.check_context(arc.open(), 'fully_trusted'):
            self.expect_file('all_bits',
                             mode=f'?rw{_suid_file}rw{_sgid_file}rw{_t_file}')
            self.expect_file('perm_bits', mode='?rwxrwxrwx')
            self.expect_file('exec_group_other', mode='?rw-rwxrwx')
            self.expect_file('read_group_only', mode='?---r-----')
            self.expect_file('no_bits', mode='?---------')
            self.expect_file('dir/', mode=f'?---rw{_sgid_dir}rw{_t_dir}')
            self.expect_file('dir_all_bits/',
                             mode=f'?rw{_suid_dir}rw{_sgid_dir}rw{_t_dir}')

        with self.check_context(arc.open(), 'tar'):
            self.expect_file('all_bits', mode='?rwxr-xr-x')
            self.expect_file('perm_bits', mode='?rwxr-xr-x')
            self.expect_file('exec_group_other', mode='?rw-r-xr-x')
            self.expect_file('read_group_only', mode='?---r-----')
            self.expect_file('no_bits', mode='?---------')
            self.expect_file('dir/', mode='?---r-xr-x')
            self.expect_file('dir_all_bits/', mode='?rwxr-xr-x')

        with self.check_context(arc.open(), 'data'):
            normal_dir_mode = stat.filemode(stat.S_IMODE(
                self.outerdir.stat().st_mode))
            self.expect_file('all_bits', mode='?rwxr-xr-x')
            self.expect_file('perm_bits', mode='?rwxr-xr-x')
            self.expect_file('exec_group_other', mode='?rw-r--r--')
            self.expect_file('read_group_only', mode='?rw-r-----')
            self.expect_file('no_bits', mode='?rw-------')
            self.expect_file('dir/', mode=normal_dir_mode)
            self.expect_file('dir_all_bits/', mode=normal_dir_mode)