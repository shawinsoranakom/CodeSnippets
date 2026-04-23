def choices(self, changelist):
        field_choices = dict(self.field.flatchoices)
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        for lookup, title, count_field in (
            (None, _("All"), None),
            ("1", field_choices.get(True, _("Yes")), "true__c"),
            ("0", field_choices.get(False, _("No")), "false__c"),
        ):
            if add_facets:
                if count_field is not None:
                    count = facet_counts[count_field]
                    title = f"{title} ({count})"
            yield {
                "selected": self.lookup_val == lookup and not self.lookup_val2,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg: lookup}, [self.lookup_kwarg2]
                ),
                "display": title,
            }
        if self.field.null:
            display = field_choices.get(None, _("Unknown"))
            if add_facets:
                count = facet_counts["null__c"]
                display = f"{display} ({count})"
            yield {
                "selected": self.lookup_val2 == "True",
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg2: "True"}, [self.lookup_kwarg]
                ),
                "display": display,
            }