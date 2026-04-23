def _check_list_filter_item(self, obj, item, label):
        """
        Check one item of `list_filter`, the three valid options are:
        1. 'field' -- a basic field filter, possibly w/ relationships (e.g.
           'field__rel')
        2. ('field', SomeFieldListFilter) - a field-based list filter class
        3. SomeListFilter - a non-field list filter class
        """
        from django.contrib.admin import FieldListFilter, ListFilter

        if callable(item) and not isinstance(item, models.Field):
            # If item is option 3, it should be a ListFilter...
            if not _issubclass(item, ListFilter):
                return must_inherit_from(
                    parent="ListFilter", option=label, obj=obj, id="admin.E113"
                )
            # ... but not a FieldListFilter.
            elif issubclass(item, FieldListFilter):
                return [
                    checks.Error(
                        "The value of '%s' must not inherit from 'FieldListFilter'."
                        % label,
                        obj=obj.__class__,
                        id="admin.E114",
                    )
                ]
            else:
                return []
        elif isinstance(item, (tuple, list)):
            # item is option #2
            field, list_filter_class = item
            if not _issubclass(list_filter_class, FieldListFilter):
                return must_inherit_from(
                    parent="FieldListFilter",
                    option="%s[1]" % label,
                    obj=obj,
                    id="admin.E115",
                )
            else:
                return []
        else:
            # item is option #1
            field = item

            # Validate the field string
            try:
                get_fields_from_path(obj.model, field)
            except (NotRelationField, FieldDoesNotExist):
                return [
                    checks.Error(
                        "The value of '%s' refers to '%s', which does not refer to a "
                        "Field." % (label, field),
                        obj=obj.__class__,
                        id="admin.E116",
                    )
                ]
            else:
                return []