def test_slicing_negative_indexing_not_supported_for_single_element(self):
        """hint: inverting your ordering might do what you need"""
        msg = "Negative indexing is not supported."
        with self.assertRaisesMessage(ValueError, msg):
            Article.objects.all()[-1]