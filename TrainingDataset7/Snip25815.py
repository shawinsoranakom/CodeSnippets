def test_values_list_flat_more_than_one_field(self):
        msg = "'flat' is not valid when values_list is called with more than one field."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.values_list("id", "headline", flat=True)