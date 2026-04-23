def mkdtemp(self):
        tmp_dir = super().mkdtemp()
        return Path(tmp_dir)