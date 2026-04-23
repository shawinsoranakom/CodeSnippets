def test_link_follow_symlinks(self):
        default_follow = sys.platform.startswith(
            ('darwin', 'freebsd', 'netbsd', 'openbsd', 'dragonfly', 'sunos5'))
        default_no_follow = sys.platform.startswith(('win32', 'linux'))
        orig = os_helper.TESTFN
        symlink = orig + 'symlink'
        posix.symlink(orig, symlink)
        self.addCleanup(os_helper.unlink, symlink)

        with self.subTest('no follow_symlinks'):
            # no follow_symlinks -> platform depending
            link = orig + 'link'
            posix.link(symlink, link)
            self.addCleanup(os_helper.unlink, link)
            if os.link in os.supports_follow_symlinks or default_follow:
                self.assertEqual(posix.lstat(link), posix.lstat(orig))
            elif default_no_follow:
                self.assertEqual(posix.lstat(link), posix.lstat(symlink))

        with self.subTest('follow_symlinks=False'):
            # follow_symlinks=False -> duplicate the symlink itself
            link = orig + 'link_nofollow'
            try:
                posix.link(symlink, link, follow_symlinks=False)
            except NotImplementedError:
                if os.link in os.supports_follow_symlinks or default_no_follow:
                    raise
            else:
                self.addCleanup(os_helper.unlink, link)
                self.assertEqual(posix.lstat(link), posix.lstat(symlink))

        with self.subTest('follow_symlinks=True'):
            # follow_symlinks=True -> duplicate the target file
            link = orig + 'link_following'
            try:
                posix.link(symlink, link, follow_symlinks=True)
            except NotImplementedError:
                if os.link in os.supports_follow_symlinks or default_follow:
                    raise
            else:
                self.addCleanup(os_helper.unlink, link)
                self.assertEqual(posix.lstat(link), posix.lstat(orig))