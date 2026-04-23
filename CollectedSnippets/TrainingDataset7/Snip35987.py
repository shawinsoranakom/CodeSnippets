def test_extract_file_permissions(self):
        """archive.extract() preserves file permissions."""
        mask = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        umask = os.umask(0)
        os.umask(umask)  # Restore the original umask.
        with os.scandir(self.testdir) as entries:
            for entry in entries:
                if (
                    entry.name.startswith("leadpath_")
                    or (entry.name.endswith(".bz2") and not HAS_BZ2)
                    or (entry.name.endswith((".lzma", ".xz")) and not HAS_LZMA)
                ):
                    continue
                with self.subTest(entry.name), tempfile.TemporaryDirectory() as tmpdir:
                    archive.extract(entry.path, tmpdir)
                    # An executable file in the archive has executable
                    # permissions.
                    filepath = os.path.join(tmpdir, "executable")
                    self.assertEqual(os.stat(filepath).st_mode & mask, 0o775)
                    # A file is readable even if permission data is missing.
                    filepath = os.path.join(tmpdir, "no_permissions")
                    self.assertEqual(os.stat(filepath).st_mode & mask, 0o666 & ~umask)