def get_prep_lookup(self):
        from django.db.models.sql.query import Query  # avoid circular import

        if isinstance(self.lhs, ColPairs):
            if (
                isinstance(self.rhs, Query)
                and not self.rhs.has_select_fields
                and self.lhs.output_field.related_model is self.rhs.model
            ):
                self.rhs.set_values([f.name for f in self.lhs.sources])
        else:
            if self.rhs_is_direct_value():
                # If we get here, we are dealing with single-column relations.
                self.rhs = [get_normalized_value(val, self.lhs)[0] for val in self.rhs]
                # We need to run the related field's get_prep_value(). Consider
                # case ForeignKey to IntegerField given value 'abc'. The
                # ForeignKey itself doesn't have validation for non-integers,
                # so we must run validation using the target field.
                if hasattr(self.lhs.output_field, "path_infos"):
                    # Run the target field's get_prep_value. We can safely
                    # assume there is only one as we don't get to the direct
                    # value branch otherwise.
                    target_field = self.lhs.output_field.path_infos[-1].target_fields[
                        -1
                    ]
                    self.rhs = [target_field.get_prep_value(v) for v in self.rhs]
            elif not getattr(self.rhs, "has_select_fields", True) and not getattr(
                self.lhs.field.target_field, "primary_key", False
            ):
                if (
                    getattr(self.lhs.output_field, "primary_key", False)
                    and self.lhs.output_field.model == self.rhs.model
                ):
                    # A case like
                    # Restaurant.objects.filter(place__in=restaurant_qs), where
                    # place is a OneToOneField and the primary key of
                    # Restaurant.
                    target_field = self.lhs.field.name
                else:
                    target_field = self.lhs.field.target_field.name
                self.rhs.set_values([target_field])
        return super().get_prep_lookup()