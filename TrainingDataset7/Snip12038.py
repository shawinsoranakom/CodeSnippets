def _check_ordering_first_last_queryset_aggregation(self, method):
        if (
            isinstance(self.query.group_by, tuple)
            # Raise if the pk fields are not in the group_by.
            and self.model._meta.pk
            not in {col.output_field for col in self.query.group_by}
            and set(self.model._meta.pk_fields).difference(
                {col.target for col in self.query.group_by}
            )
        ):
            raise TypeError(
                f"Cannot use QuerySet.{method}() on an unordered queryset performing "
                f"aggregation. Add an ordering with order_by()."
            )