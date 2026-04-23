def test_clean(self):
        result = config_util._clean(" clean    this         text  ")
        self.assertEqual("clean this text", result)