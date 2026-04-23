def generate_deleted_models(self):
        """
        Find all deleted models (managed and unmanaged) and make delete
        operations for them as well as separate operations to delete any
        foreign key or M2M relationships (these are optimized later, if
        possible).

        Also bring forward removal of any model options that refer to
        collections of fields - the inverse of generate_created_models().
        """
        new_keys = self.new_model_keys | self.new_unmanaged_keys
        deleted_models = self.old_model_keys - new_keys
        deleted_unmanaged_models = self.old_unmanaged_keys - new_keys
        all_deleted_models = chain(
            sorted(deleted_models), sorted(deleted_unmanaged_models)
        )
        for app_label, model_name in all_deleted_models:
            model_state = self.from_state.models[app_label, model_name]
            # Gather related fields
            related_fields = {}
            for field_name, field in model_state.fields.items():
                if field.remote_field:
                    if field.remote_field.model:
                        related_fields[field_name] = field
                    if getattr(field.remote_field, "through", None):
                        related_fields[field_name] = field
            # Generate option removal first
            unique_together = model_state.options.pop("unique_together", None)
            if unique_together:
                self.add_operation(
                    app_label,
                    operations.AlterUniqueTogether(
                        name=model_name,
                        unique_together=None,
                    ),
                )
            if indexes := model_state.options.pop("indexes", None):
                for index in indexes:
                    self.add_operation(
                        app_label,
                        operations.RemoveIndex(
                            model_name=model_name,
                            name=index.name,
                        ),
                    )
            if constraints := model_state.options.pop("constraints", None):
                for constraint in constraints:
                    self.add_operation(
                        app_label,
                        operations.RemoveConstraint(
                            model_name=model_name,
                            name=constraint.name,
                        ),
                    )
            # Then remove each related field
            for name in sorted(related_fields):
                self.add_operation(
                    app_label,
                    operations.RemoveField(
                        model_name=model_name,
                        name=name,
                    ),
                    dependencies=[
                        OperationDependency(
                            app_label,
                            model_name,
                            name,
                            OperationDependency.Type.REMOVE_INDEX_OR_CONSTRAINT,
                        ),
                    ],
                )
            # Finally, remove the model.
            # This depends on both the removal/alteration of all incoming
            # fields and the removal of all its own related fields, and if it's
            # a through model the field that references it.
            dependencies = []
            relations = self.from_state.relations
            for (
                related_object_app_label,
                object_name,
            ), relation_related_fields in relations[app_label, model_name].items():
                for field_name, field in relation_related_fields.items():
                    dependencies.append(
                        OperationDependency(
                            related_object_app_label,
                            object_name,
                            field_name,
                            OperationDependency.Type.REMOVE,
                        ),
                    )
                    if not field.many_to_many:
                        dependencies.append(
                            OperationDependency(
                                related_object_app_label,
                                object_name,
                                field_name,
                                OperationDependency.Type.ALTER,
                            ),
                        )

            for name in sorted(related_fields):
                dependencies.append(
                    OperationDependency(
                        app_label, model_name, name, OperationDependency.Type.REMOVE
                    )
                )
            # We're referenced in another field's through=
            through_user = self.through_users.get((app_label, model_state.name_lower))
            if through_user:
                dependencies.append(
                    OperationDependency(*through_user, OperationDependency.Type.REMOVE),
                )
            # Finally, make the operation, deduping any dependencies
            self.add_operation(
                app_label,
                operations.DeleteModel(
                    name=model_state.name,
                ),
                dependencies=list(set(dependencies)),
            )