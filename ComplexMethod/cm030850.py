def glob(self, *parts, **kwargs):
        if len(parts) == 1:
            pattern = parts[0]
        else:
            pattern = os.path.join(*parts)
        p = os.path.join(self.tempdir, pattern)
        res = glob.glob(p, **kwargs)
        res2 = glob.iglob(p, **kwargs)
        self.assertCountEqual(glob.iglob(p, **kwargs), res)

        bres = [os.fsencode(x) for x in res]
        self.assertCountEqual(glob.glob(os.fsencode(p), **kwargs), bres)
        self.assertCountEqual(glob.iglob(os.fsencode(p), **kwargs), bres)

        with change_cwd(self.tempdir):
            res2 = glob.glob(pattern, **kwargs)
            for x in res2:
                self.assertFalse(os.path.isabs(x), x)
            if pattern == '**' or pattern == '**' + os.sep:
                expected = res[1:]
            else:
                expected = res
            self.assertCountEqual([os.path.join(self.tempdir, x) for x in res2],
                                  expected)
            self.assertCountEqual(glob.iglob(pattern, **kwargs), res2)
            bpattern = os.fsencode(pattern)
            bres2 = [os.fsencode(x) for x in res2]
            self.assertCountEqual(glob.glob(bpattern, **kwargs), bres2)
            self.assertCountEqual(glob.iglob(bpattern, **kwargs), bres2)

        self.assertCountEqual(glob.glob(pattern, root_dir=self.tempdir, **kwargs), res2)
        self.assertCountEqual(glob.iglob(pattern, root_dir=self.tempdir, **kwargs), res2)
        btempdir = os.fsencode(self.tempdir)
        self.assertCountEqual(
            glob.glob(bpattern, root_dir=btempdir, **kwargs), bres2)
        self.assertCountEqual(
            glob.iglob(bpattern, root_dir=btempdir, **kwargs), bres2)

        if self.dir_fd is not None:
            self.assertCountEqual(
                glob.glob(pattern, dir_fd=self.dir_fd, **kwargs), res2)
            self.assertCountEqual(
                glob.iglob(pattern, dir_fd=self.dir_fd, **kwargs), res2)
            self.assertCountEqual(
                glob.glob(bpattern, dir_fd=self.dir_fd, **kwargs), bres2)
            self.assertCountEqual(
                glob.iglob(bpattern, dir_fd=self.dir_fd, **kwargs), bres2)

        return res