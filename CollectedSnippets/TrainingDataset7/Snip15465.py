def test_get_facet_counts(self):
        msg = "subclasses of FacetsMixin must provide a get_facet_counts() method."
        with self.assertRaisesMessage(NotImplementedError, msg):
            FacetsMixin().get_facet_counts(None, None)