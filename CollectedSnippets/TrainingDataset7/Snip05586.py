def _check_extra(self, obj):
        """Check that extra is an integer."""

        if not isinstance(obj.extra, int):
            return must_be("an integer", option="extra", obj=obj, id="admin.E203")
        else:
            return []