def assertNoneExist(self, dir, langs):
        self.assertTrue(
            all(Path(self.MO_FILE % (dir, lang)).exists() is False for lang in langs)
        )