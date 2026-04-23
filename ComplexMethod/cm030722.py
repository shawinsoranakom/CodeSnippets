def nameCheck(self, name, dir, pre, suf):
        (ndir, nbase) = os.path.split(name)
        npre  = nbase[:len(pre)]
        nsuf  = nbase[len(nbase)-len(suf):]

        if dir is not None:
            self.assertIs(
                type(name),
                str
                if type(dir) is str or isinstance(dir, os.PathLike) else
                bytes,
                "unexpected return type",
            )
        if pre is not None:
            self.assertIs(type(name), str if type(pre) is str else bytes,
                          "unexpected return type")
        if suf is not None:
            self.assertIs(type(name), str if type(suf) is str else bytes,
                          "unexpected return type")
        if (dir, pre, suf) == (None, None, None):
            self.assertIs(type(name), str, "default return type must be str")

        # check for equality of the absolute paths!
        self.assertEqual(os.path.abspath(ndir), os.path.abspath(dir),
                         "file %r not in directory %r" % (name, dir))
        self.assertEqual(npre, pre,
                         "file %r does not begin with %r" % (nbase, pre))
        self.assertEqual(nsuf, suf,
                         "file %r does not end with %r" % (nbase, suf))

        nbase = nbase[len(pre):len(nbase)-len(suf)]
        check = self.str_check if isinstance(nbase, str) else self.b_check
        self.assertTrue(check.match(nbase),
                        "random characters %r do not match %r"
                        % (nbase, check.pattern))