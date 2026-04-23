def _check_relationship_model(self, from_model=None, **kwargs):
        from django.db.models.fields.composite import CompositePrimaryKey

        if hasattr(self.remote_field.through, "_meta"):
            qualified_model_name = "%s.%s" % (
                self.remote_field.through._meta.app_label,
                self.remote_field.through.__name__,
            )
        else:
            qualified_model_name = self.remote_field.through

        errors = []

        if self.remote_field.through not in self.opts.apps.get_models(
            include_auto_created=True
        ):
            # The relationship model is not installed.
            errors.append(
                checks.Error(
                    "Field specifies a many-to-many relation through model "
                    "'%s', which has not been installed." % qualified_model_name,
                    obj=self,
                    id="fields.E331",
                )
            )

        else:
            assert from_model is not None, (
                "ManyToManyField with intermediate "
                "tables cannot be checked if you don't pass the model "
                "where the field is attached to."
            )
            # Set some useful local variables
            to_model = resolve_relation(from_model, self.remote_field.model)
            from_model_name = from_model._meta.object_name
            if isinstance(to_model, str):
                to_model_name = to_model
            else:
                to_model_name = to_model._meta.object_name
            if self.remote_field.through_fields is None and not isinstance(
                to_model, str
            ):
                model_name = None
                if isinstance(to_model._meta.pk, CompositePrimaryKey):
                    model_name = self.remote_field.model._meta.object_name
                elif isinstance(from_model._meta.pk, CompositePrimaryKey):
                    model_name = from_model_name
                if model_name:
                    errors.append(
                        checks.Error(
                            f"Field defines a relation involving model {model_name!r} "
                            "which has a CompositePrimaryKey and such relations are "
                            "not supported.",
                            obj=self,
                            id="fields.E347",
                        )
                    )
            relationship_model_name = self.remote_field.through._meta.object_name
            self_referential = from_model == to_model
            # Count foreign keys in intermediate model
            if self_referential:
                seen_self = sum(
                    from_model == getattr(field.remote_field, "model", None)
                    for field in self.remote_field.through._meta.fields
                )

                if seen_self > 2 and not self.remote_field.through_fields:
                    errors.append(
                        checks.Error(
                            "The model is used as an intermediate model by "
                            "'%s', but it has more than two foreign keys "
                            "to '%s', which is ambiguous. You must specify "
                            "which two foreign keys Django should use via the "
                            "through_fields keyword argument."
                            % (self, from_model_name),
                            hint=(
                                "Use through_fields to specify which two foreign keys "
                                "Django should use."
                            ),
                            obj=self.remote_field.through,
                            id="fields.E333",
                        )
                    )

            else:
                # Count foreign keys in relationship model
                seen_from = sum(
                    from_model == getattr(field.remote_field, "model", None)
                    for field in self.remote_field.through._meta.fields
                )
                seen_to = sum(
                    to_model == getattr(field.remote_field, "model", None)
                    for field in self.remote_field.through._meta.fields
                )

                if seen_from > 1 and not self.remote_field.through_fields:
                    errors.append(
                        checks.Error(
                            (
                                "The model is used as an intermediate model by "
                                "'%s', but it has more than one foreign key "
                                "from '%s', which is ambiguous. You must specify "
                                "which foreign key Django should use via the "
                                "through_fields keyword argument."
                            )
                            % (self, from_model_name),
                            hint=(
                                "If you want to create a recursive relationship, "
                                'use ManyToManyField("%s", through="%s").'
                            )
                            % (
                                RECURSIVE_RELATIONSHIP_CONSTANT,
                                relationship_model_name,
                            ),
                            obj=self,
                            id="fields.E334",
                        )
                    )

                if seen_to > 1 and not self.remote_field.through_fields:
                    errors.append(
                        checks.Error(
                            "The model is used as an intermediate model by "
                            "'%s', but it has more than one foreign key "
                            "to '%s', which is ambiguous. You must specify "
                            "which foreign key Django should use via the "
                            "through_fields keyword argument." % (self, to_model_name),
                            hint=(
                                "If you want to create a recursive relationship, "
                                'use ManyToManyField("%s", through="%s").'
                            )
                            % (
                                RECURSIVE_RELATIONSHIP_CONSTANT,
                                relationship_model_name,
                            ),
                            obj=self,
                            id="fields.E335",
                        )
                    )

                if seen_from == 0 or seen_to == 0:
                    errors.append(
                        checks.Error(
                            "The model is used as an intermediate model by "
                            "'%s', but it does not have a foreign key to '%s' or '%s'."
                            % (self, from_model_name, to_model_name),
                            obj=self.remote_field.through,
                            id="fields.E336",
                        )
                    )

        # Validate `through_fields`.
        if self.remote_field.through_fields is not None:
            # Validate that we're given an iterable of at least two items
            # and that none of them is "falsy".
            if not (
                len(self.remote_field.through_fields) >= 2
                and self.remote_field.through_fields[0]
                and self.remote_field.through_fields[1]
            ):
                errors.append(
                    checks.Error(
                        "Field specifies 'through_fields' but does not provide "
                        "the names of the two link fields that should be used "
                        "for the relation through model '%s'." % qualified_model_name,
                        hint=(
                            "Make sure you specify 'through_fields' as "
                            "through_fields=('field1', 'field2')"
                        ),
                        obj=self,
                        id="fields.E337",
                    )
                )

            # Validate the given through fields -- they should be actual
            # fields on the through model, and also be foreign keys to the
            # expected models.
            else:
                assert from_model is not None, (
                    "ManyToManyField with intermediate "
                    "tables cannot be checked if you don't pass the model "
                    "where the field is attached to."
                )

                source, through, target = (
                    from_model,
                    self.remote_field.through,
                    self.remote_field.model,
                )
                source_field_name, target_field_name = self.remote_field.through_fields[
                    :2
                ]

                for field_name, related_model in (
                    (source_field_name, source),
                    (target_field_name, target),
                ):
                    possible_field_names = []
                    for f in through._meta.fields:
                        if (
                            hasattr(f, "remote_field")
                            and getattr(f.remote_field, "model", None) == related_model
                        ):
                            possible_field_names.append(f.name)
                    if possible_field_names:
                        hint = (
                            "Did you mean one of the following foreign keys to '%s': "
                            "%s?"
                            % (
                                related_model._meta.object_name,
                                ", ".join(possible_field_names),
                            )
                        )
                    else:
                        hint = None

                    try:
                        field = through._meta.get_field(field_name)
                    except exceptions.FieldDoesNotExist:
                        errors.append(
                            checks.Error(
                                "The intermediary model '%s' has no field '%s'."
                                % (qualified_model_name, field_name),
                                hint=hint,
                                obj=self,
                                id="fields.E338",
                            )
                        )
                    else:
                        if not (
                            hasattr(field, "remote_field")
                            and getattr(field.remote_field, "model", None)
                            == related_model
                        ):
                            related_object_name = (
                                related_model
                                if isinstance(related_model, str)
                                else related_model._meta.object_name
                            )
                            errors.append(
                                checks.Error(
                                    "'%s.%s' is not a foreign key to '%s'."
                                    % (
                                        through._meta.object_name,
                                        field_name,
                                        related_object_name,
                                    ),
                                    hint=hint,
                                    obj=self,
                                    id="fields.E339",
                                )
                            )

        return errors