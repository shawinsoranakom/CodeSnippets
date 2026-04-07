def test_failure_finding_default_mo_files(self):
        """OSError is raised if the default language is unparseable."""
        self.patchGettextFind()
        trans_real._translations = {}
        with self.assertRaises(OSError):
            activate("en")