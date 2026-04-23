def expect_file(self, name, type=None, symlink_to=None, mode=None,
                    size=None, content=None):
        """Check a single file. See check_context."""
        if self.raised_exception:
            raise self.raised_exception
        # use normpath() rather than resolve() so we don't follow symlinks
        path = pathlib.Path(os.path.normpath(self.destdir / name))
        self.assertIn(path, self.expected_paths)
        self.expected_paths.remove(path)
        if mode is not None and os_helper.can_chmod() and os.name != 'nt':
            got = stat.filemode(stat.S_IMODE(path.stat().st_mode))
            self.assertEqual(got, mode)
        if type is None and isinstance(name, str) and name.endswith('/'):
            type = tarfile.DIRTYPE
        if symlink_to is not None:
            got = (self.destdir / name).readlink()
            expected = pathlib.Path(symlink_to)
            # The symlink might be the same (textually) as what we expect,
            # but some systems change the link to an equivalent path, so
            # we fall back to samefile().
            try:
                if expected != got:
                    self.assertTrue(got.samefile(expected))
            except Exception as e:
                # attach a note, so it's shown even if `samefile` fails
                e.add_note(f'{expected=}, {got=}')
                raise
        elif type == tarfile.REGTYPE or type is None:
            self.assertTrue(path.is_file())
        elif type == tarfile.DIRTYPE:
            self.assertTrue(path.is_dir())
        elif type == tarfile.FIFOTYPE:
            self.assertTrue(path.is_fifo())
        elif type == tarfile.SYMTYPE:
            self.assertTrue(path.is_symlink())
        else:
            raise NotImplementedError(type)
        if size is not None:
            self.assertEqual(path.stat().st_size, size)
        if content is not None:
            self.assertEqual(path.read_text(), content)
        for parent in path.parents:
            self.expected_paths.discard(parent)