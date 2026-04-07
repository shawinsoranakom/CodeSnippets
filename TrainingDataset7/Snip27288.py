def test_create_model2(self):
        """
        Test when router returns False (i.e. CreateModel shouldn't run).
        """
        self._test_create_model("test_mltdb_crmo2", should_run=False)