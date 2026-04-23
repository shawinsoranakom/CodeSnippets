def test_get_dirs(self):
        inner_dirs = self.engine.template_loaders[0].loaders[0].get_dirs()
        self.assertSequenceEqual(
            list(self.engine.template_loaders[0].get_dirs()), list(inner_dirs)
        )