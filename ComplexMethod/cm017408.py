def _check_clashes(self):
        """Check accessor and reverse query name clashes."""
        from django.db.models.base import ModelBase

        errors = []
        opts = self.model._meta

        # f.remote_field.model may be a string instead of a model. Skip if
        # model name is not resolved.
        if not isinstance(self.remote_field.model, ModelBase):
            return []

        # Consider that we are checking field `Model.foreign` and the models
        # are:
        #
        #     class Target(models.Model):
        #         model = models.IntegerField()
        #         model_set = models.IntegerField()
        #
        #     class Model(models.Model):
        #         foreign = models.ForeignKey(Target)
        #         m2m = models.ManyToManyField(Target)

        # rel_opts.object_name == "Target"
        rel_opts = self.remote_field.model._meta
        # If the field doesn't install a backward relation on the target model
        # (so `is_hidden` returns True), then there are no clashes to check
        # and we can skip these fields.
        rel_is_hidden = self.remote_field.hidden
        rel_name = self.remote_field.accessor_name  # i. e. "model_set"
        rel_query_name = self.related_query_name()  # i. e. "model"
        # i.e. "app_label.Model.field".
        field_name = "%s.%s" % (opts.label, self.name)

        # Check clashes between accessor or reverse query name of `field`
        # and any other field name -- i.e. accessor for Model.foreign is
        # model_set and it clashes with Target.model_set.
        potential_clashes = rel_opts.fields + rel_opts.many_to_many
        for clash_field in potential_clashes:
            if not rel_is_hidden and clash_field.name == rel_name:
                clash_name = f"{rel_opts.label}.{clash_field.name}"
                errors.append(
                    checks.Error(
                        f"Reverse accessor '{rel_opts.object_name}.{rel_name}' "
                        f"for '{field_name}' clashes with field name "
                        f"'{clash_name}'.",
                        hint=(
                            "Rename field '%s', or add/change a related_name "
                            "argument to the definition for field '%s'."
                        )
                        % (clash_name, field_name),
                        obj=self,
                        id="fields.E302",
                    )
                )

            if clash_field.name == rel_query_name:
                clash_name = f"{rel_opts.label}.{clash_field.name}"
                errors.append(
                    checks.Error(
                        "Reverse query name for '%s' clashes with field name '%s'."
                        % (field_name, clash_name),
                        hint=(
                            "Rename field '%s', or add/change a related_name "
                            "argument to the definition for field '%s'."
                        )
                        % (clash_name, field_name),
                        obj=self,
                        id="fields.E303",
                    )
                )

        # Check clashes between accessors/reverse query names of `field` and
        # any other field accessor -- i. e. Model.foreign accessor clashes with
        # Model.m2m accessor.
        potential_clashes = (r for r in rel_opts.related_objects if r.field is not self)
        for clash_field in potential_clashes:
            if not rel_is_hidden and clash_field.accessor_name == rel_name:
                clash_name = (
                    f"{clash_field.related_model._meta.label}.{clash_field.field.name}"
                )
                errors.append(
                    checks.Error(
                        f"Reverse accessor '{rel_opts.object_name}.{rel_name}' "
                        f"for '{field_name}' clashes with reverse accessor for "
                        f"'{clash_name}'.",
                        hint=(
                            "Add or change a related_name argument "
                            "to the definition for '%s' or '%s'."
                        )
                        % (field_name, clash_name),
                        obj=self,
                        id="fields.E304",
                    )
                )

            if clash_field.accessor_name == rel_query_name:
                clash_name = (
                    f"{clash_field.related_model._meta.label}.{clash_field.field.name}"
                )
                errors.append(
                    checks.Error(
                        "Reverse query name for '%s' clashes with reverse query name "
                        "for '%s'." % (field_name, clash_name),
                        hint=(
                            "Add or change a related_name argument "
                            "to the definition for '%s' or '%s'."
                        )
                        % (field_name, clash_name),
                        obj=self,
                        id="fields.E305",
                    )
                )

        # Check clash between reverse accessor and manager names on
        # the target model.
        if not rel_is_hidden:
            manager_names = {m.name for m in rel_opts.managers}
            if rel_name in manager_names:
                errors.append(
                    checks.Error(
                        f"Related name '{rel_name}' for '{field_name}' "
                        f"clashes with the name of a model manager.",
                        hint=(
                            "Rename the model manager or change the related_name "
                            "argument in the definition for field '%s'." % field_name
                        ),
                        obj=self,
                        id="fields.E348",
                    )
                )

        return errors