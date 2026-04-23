def test_copy_dir_preserve_metadata(self):
        base = self.cls(self.base)
        source = base / 'dirC'
        if hasattr(os, 'chmod'):
            os.chmod(source / 'dirD', stat.S_IRWXU | stat.S_IRWXO)
        if hasattr(os, 'chflags') and hasattr(stat, 'UF_NODUMP'):
            os.chflags(source / 'fileC', stat.UF_NODUMP)
        target = base / 'copyA'

        subpaths = ['.', 'fileC', 'dirD', 'dirD/fileD']
        source_sts = [source.joinpath(subpath).stat() for subpath in subpaths]
        source.copy(target, preserve_metadata=True)
        target_sts = [target.joinpath(subpath).stat() for subpath in subpaths]

        for source_st, target_st in zip(source_sts, target_sts):
            self.assertLessEqual(source_st.st_atime, target_st.st_atime)
            self.assertLessEqual(source_st.st_mtime, target_st.st_mtime)
            self.assertEqual(source_st.st_mode, target_st.st_mode)
            if hasattr(source_st, 'st_flags'):
                self.assertEqual(source_st.st_flags, target_st.st_flags)