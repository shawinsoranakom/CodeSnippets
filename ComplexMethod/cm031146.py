def symlink_or_copy(self, src, dst, relative_symlinks_ok=False):
        """
        Try symlinking a file, and if that fails, fall back to copying.
        (Unused on Windows, because we can't just copy a failed symlink file: we
        switch to a different set of files instead.)
        """
        assert os.name != 'nt'
        force_copy = not self.symlinks
        if not force_copy:
            try:
                if not os.path.islink(dst):  # can't link to itself!
                    if relative_symlinks_ok:
                        assert os.path.dirname(src) == os.path.dirname(dst)
                        os.symlink(os.path.basename(src), dst)
                    else:
                        os.symlink(src, dst)
            except Exception:   # may need to use a more specific exception
                logger.warning('Unable to symlink %r to %r', src, dst)
                force_copy = True
        if force_copy:
            shutil.copyfile(src, dst)