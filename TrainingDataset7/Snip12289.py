def add_fields(self, field_names, allow_m2m=True):
        """
        Add the given (model) fields to the select set. Add the field names in
        the order specified.
        """
        alias = self.get_initial_alias()
        opts = self.get_meta()

        try:
            cols = []
            for name in field_names:
                # Join promotion note - we must not remove any rows here, so
                # if there is no existing joins, use outer join.
                join_info = self.setup_joins(
                    name.split(LOOKUP_SEP), opts, alias, allow_many=allow_m2m
                )
                targets, final_alias, joins = self.trim_joins(
                    join_info.targets,
                    join_info.joins,
                    join_info.path,
                )
                if len(targets) > 1:
                    transformed_targets = [
                        join_info.transform_function(target, final_alias)
                        for target in targets
                    ]
                    cols.append(
                        ColPairs(
                            final_alias if self.alias_cols else None,
                            [col.target for col in transformed_targets],
                            [col.output_field for col in transformed_targets],
                            join_info.final_field,
                        )
                    )
                else:
                    cols.append(join_info.transform_function(targets[0], final_alias))
            if cols:
                self.set_select(cols)
        except MultiJoin:
            raise FieldError("Invalid field name: '%s'" % name)
        except FieldError:
            if LOOKUP_SEP in name:
                # For lookups spanning over relationships, show the error
                # from the model on which the lookup failed.
                raise
            else:
                names = sorted(
                    [
                        *get_field_names_from_opts(opts),
                        *self.extra,
                        *self.annotation_select,
                        *self._filtered_relations,
                    ]
                )
                raise FieldError(
                    "Cannot resolve keyword %r into field. "
                    "Choices are: %s" % (name, ", ".join(names))
                )