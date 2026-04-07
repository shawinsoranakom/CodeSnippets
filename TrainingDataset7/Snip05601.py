def get_facet_counts(self, pk_attname, filtered_qs):
        raise NotImplementedError(
            "subclasses of FacetsMixin must provide a get_facet_counts() method."
        )