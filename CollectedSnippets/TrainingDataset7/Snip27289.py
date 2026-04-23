def test_create_model3(self):
        """
        Test when router returns True (i.e. CreateModel should run).
        """
        self._test_create_model("test_mltdb_crmo3", should_run=True)