def test_copy2_symlinks(self):
        tmp_dir = self.mkdtemp()
        src = os.path.join(tmp_dir, 'foo')
        dst = os.path.join(tmp_dir, 'bar')
        src_link = os.path.join(tmp_dir, 'baz')
        create_file(src, 'foo')
        os.symlink(src, src_link)
        if hasattr(os, 'lchmod'):
            os.lchmod(src_link, stat.S_IRWXU | stat.S_IRWXO)
        if hasattr(os, 'lchflags') and hasattr(stat, 'UF_NODUMP'):
            os.lchflags(src_link, stat.UF_NODUMP)
        src_stat = os.stat(src)
        src_link_stat = os.lstat(src_link)
        # follow
        shutil.copy2(src_link, dst, follow_symlinks=True)
        self.assertFalse(os.path.islink(dst))
        self.assertEqual(read_file(src), read_file(dst))
        os.remove(dst)
        # don't follow
        shutil.copy2(src_link, dst, follow_symlinks=False)
        self.assertTrue(os.path.islink(dst))
        self.assertEqual(os.readlink(dst), os.readlink(src_link))
        dst_stat = os.lstat(dst)
        if os.utime in os.supports_follow_symlinks:
            for attr in 'st_atime', 'st_mtime':
                # The modification times may be truncated in the new file.
                self.assertLessEqual(getattr(src_link_stat, attr),
                                     getattr(dst_stat, attr) + 1)
        if hasattr(os, 'lchmod'):
            self.assertEqual(src_link_stat.st_mode, dst_stat.st_mode)
            self.assertNotEqual(src_stat.st_mode, dst_stat.st_mode)
        if hasattr(os, 'lchflags') and hasattr(src_link_stat, 'st_flags'):
            self.assertEqual(src_link_stat.st_flags, dst_stat.st_flags)