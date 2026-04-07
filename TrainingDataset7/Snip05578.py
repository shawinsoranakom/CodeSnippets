def _check_list_editable(self, obj):
        """Check that list_editable is a sequence of editable fields from
        list_display without first element."""

        if not isinstance(obj.list_editable, (list, tuple)):
            return must_be(
                "a list or tuple", option="list_editable", obj=obj, id="admin.E120"
            )
        else:
            return list(
                chain.from_iterable(
                    self._check_list_editable_item(
                        obj, item, "list_editable[%d]" % index
                    )
                    for index, item in enumerate(obj.list_editable)
                )
            )