def _rmrf(self, dname):
        if (
            os.path.commonprefix([self.test_dir, os.path.abspath(dname)])
            != self.test_dir
        ):
            return
        shutil.rmtree(dname)