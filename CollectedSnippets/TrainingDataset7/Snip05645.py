def choices(self, changelist):
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        for lookup, title, count_field in (
            (None, _("All"), None),
            ("1", _("Empty"), "empty__c"),
            ("0", _("Not empty"), "not_empty__c"),
        ):
            if add_facets:
                if count_field is not None:
                    count = facet_counts[count_field]
                    title = f"{title} ({count})"
            yield {
                "selected": self.lookup_val == lookup,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg: lookup}
                ),
                "display": title,
            }