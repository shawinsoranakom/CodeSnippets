def test_explicitpk_unspecified(self):
        """Test for primary_key being in the form and failing validation."""
        form = ExplicitPKForm({"key": "", "desc": ""})
        self.assertFalse(form.is_valid())