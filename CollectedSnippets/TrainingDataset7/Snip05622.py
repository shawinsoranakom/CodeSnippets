def choices(self, changelist):
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        yield {
            "selected": self.lookup_val is None and not self.lookup_val_isnull,
            "query_string": changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]
            ),
            "display": _("All"),
        }
        count = None
        for pk_val, val in self.lookup_choices:
            if add_facets:
                count = facet_counts[f"{pk_val}__c"]
                val = f"{val} ({count})"
            yield {
                "selected": self.lookup_val is not None
                and str(pk_val) in self.lookup_val,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg: pk_val}, [self.lookup_kwarg_isnull]
                ),
                "display": val,
            }
        empty_title = self.empty_value_display
        if self.include_empty_choice:
            if add_facets:
                count = facet_counts["__c"]
                empty_title = f"{empty_title} ({count})"
            yield {
                "selected": bool(self.lookup_val_isnull),
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg_isnull: "True"}, [self.lookup_kwarg]
                ),
                "display": empty_title,
            }