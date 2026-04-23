def expected_from_queryset(qs):
            return [
                " ".join("-" if i is None else i for i in item)
                for item in qs.values_list(
                    "name", "parent__name", "parent__parent__name"
                )
            ]