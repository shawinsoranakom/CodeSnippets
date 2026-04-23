def _check_list_max_show_all(self, obj):
        """Check that list_max_show_all is an integer."""

        if not isinstance(obj.list_max_show_all, int):
            return must_be(
                "an integer", option="list_max_show_all", obj=obj, id="admin.E119"
            )
        else:
            return []