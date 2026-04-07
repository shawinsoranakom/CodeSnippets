def _check_list_per_page(self, obj):
        """Check that list_per_page is an integer."""

        if not isinstance(obj.list_per_page, int):
            return must_be(
                "an integer", option="list_per_page", obj=obj, id="admin.E118"
            )
        else:
            return []