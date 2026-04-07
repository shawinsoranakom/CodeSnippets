def test_field_can_be_called_exact(self):
        # Make sure related managers core filters don't include an
        # explicit `__exact` lookup that could be interpreted as a
        # reference to a foreign `exact` field. refs #23940.
        related = RelatedModel.objects.create(exact=False)
        relation = related.test_fk.create()
        self.assertEqual(related.test_fk.get(), relation)