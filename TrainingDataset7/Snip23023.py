def test_html_safe(self):
        formset = self.make_choiceformset()
        self.assertTrue(hasattr(formset, "__html__"))
        self.assertEqual(str(formset), formset.__html__())