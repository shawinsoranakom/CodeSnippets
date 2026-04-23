def choices(self, changelist):
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        yield {
            "selected": self.lookup_val is None and self.lookup_val_isnull is None,
            "query_string": changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]
            ),
            "display": _("All"),
        }
        include_none = False
        count = None
        empty_title = self.empty_value_display
        for i, val in enumerate(self.lookup_choices):
            if add_facets:
                count = facet_counts[f"{i}__c"]
            if val is None:
                include_none = True
                empty_title = f"{empty_title} ({count})" if add_facets else empty_title
                continue
            val = str(val)
            yield {
                "selected": self.lookup_val is not None and val in self.lookup_val,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg: val}, [self.lookup_kwarg_isnull]
                ),
                "display": f"{val} ({count})" if add_facets else val,
            }
        if include_none:
            yield {
                "selected": bool(self.lookup_val_isnull),
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg_isnull: "True"}, [self.lookup_kwarg]
                ),
                "display": empty_title,
            }