def source_checker(self, dirs):
        loader = self.engine.template_loaders[0]

        def check_sources(path, expected_sources):
            expected_sources = [os.path.abspath(s) for s in expected_sources]
            self.assertEqual(
                [origin.name for origin in loader.get_template_sources(path)],
                expected_sources,
            )

        with self.set_dirs(dirs):
            yield check_sources