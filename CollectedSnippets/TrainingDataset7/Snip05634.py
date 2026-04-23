def choices(self, changelist):
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist) if add_facets else None
        for i, (title, param_dict) in enumerate(self.links):
            param_dict_str = {key: str(value) for key, value in param_dict.items()}
            if add_facets:
                count = facet_counts[f"{i}__c"]
                title = f"{title} ({count})"
            yield {
                "selected": self.date_params == param_dict_str,
                "query_string": changelist.get_query_string(
                    param_dict_str, [self.field_generic]
                ),
                "display": title,
            }