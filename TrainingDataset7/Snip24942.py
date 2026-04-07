def assertAllExist(self, dir, langs):
        self.assertTrue(
            all(Path(self.MO_FILE % (dir, lang)).exists() for lang in langs)
        )