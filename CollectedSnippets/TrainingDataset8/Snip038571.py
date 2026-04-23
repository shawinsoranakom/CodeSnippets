def tearDown(self):
        for p in self.patches:
            p.stop()

        try:
            del os.environ["TEST_ENV_VAR"]
        except Exception:
            pass
        config._delete_option("_test.tomlTest")