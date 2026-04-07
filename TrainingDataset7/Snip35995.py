def temporary_file(self, filename):
        dirname = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, dirname)
        return Path(dirname) / filename