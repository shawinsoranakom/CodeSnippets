def generate_created_models(self):
        """
        Find all new models (both managed and unmanaged) and make create
        operations for them as well as separate operations to create any
        foreign key or M2M relationships (these are optimized later, if
        possible).

        Defer any model options that refer to collections of fields that might
        be deferred (e.g. unique_together).
        """
        old_keys = self.old_model_keys | self.old_unmanaged_keys
        added_models = self.new_model_keys - old_keys
        added_unmanaged_models = self.new_unmanaged_keys - old_keys
        all_added_models = chain(
            sorted(added_models, key=self.swappable_first_key, reverse=True),
            sorted(added_unmanaged_models, key=self.swappable_first_key, reverse=True),
        )
        for app_label, model_name in all_added_models:
            model_state = self.to_state.models[app_label, model_name]
            # Gather related fields
            related_fields = {}
            primary_key_rel = None
            for field_name, field in model_state.fields.items():
                if field.remote_field:
                    if field.remote_field.model:
                        if field.primary_key:
                            primary_key_rel = field.remote_field.model
                        elif not field.remote_field.parent_link:
                            related_fields[field_name] = field
                    if getattr(field.remote_field, "through", None):
                        related_fields[field_name] = field

            # Are there indexes/unique_together to defer?
            indexes = model_state.options.pop("indexes")
            constraints = model_state.options.pop("constraints")
            unique_together = model_state.options.pop("unique_together", None)
            order_with_respect_to = model_state.options.pop(
                "order_with_respect_to", None
            )
            # Depend on the deletion of any possible proxy version of us
            dependencies = [
                OperationDependency(
                    app_label, model_name, None, OperationDependency.Type.REMOVE
                ),
            ]
            # Depend on all bases
            for base in model_state.bases:
                if isinstance(base, str) and "." in base:
                    base_app_label, base_name = base.split(".", 1)
                    dependencies.append(
                        OperationDependency(
                            base_app_label,
                            base_name,
                            None,
                            OperationDependency.Type.CREATE,
                        )
                    )
                    # Depend on the removal of base fields if the new model has
                    # a field with the same name.
                    old_base_model_state = self.from_state.models.get(
                        (base_app_label, base_name)
                    )
                    new_base_model_state = self.to_state.models.get(
                        (base_app_label, base_name)
                    )
                    if old_base_model_state and new_base_model_state:
                        removed_base_fields = (
                            set(old_base_model_state.fields)
                            .difference(
                                new_base_model_state.fields,
                            )
                            .intersection(model_state.fields)
                        )
                        for removed_base_field in removed_base_fields:
                            dependencies.append(
                                OperationDependency(
                                    base_app_label,
                                    base_name,
                                    removed_base_field,
                                    OperationDependency.Type.REMOVE,
                                )
                            )
            # Depend on the other end of the primary key if it's a relation
            if primary_key_rel:
                dependencies.append(
                    OperationDependency(
                        *resolve_relation(primary_key_rel, app_label, model_name),
                        None,
                        OperationDependency.Type.CREATE,
                    ),
                )
            # Generate creation operation
            self.add_operation(
                app_label,
                operations.CreateModel(
                    name=model_state.name,
                    fields=[
                        d
                        for d in model_state.fields.items()
                        if d[0] not in related_fields
                    ],
                    options=model_state.options,
                    bases=model_state.bases,
                    managers=model_state.managers,
                ),
                dependencies=dependencies,
                beginning=True,
            )

            # Don't add operations which modify the database for unmanaged
            # models
            if not model_state.options.get("managed", True):
                continue

            # Generate operations for each related field
            for name, field in sorted(related_fields.items()):
                dependencies = self._get_dependencies_for_foreign_key(
                    app_label,
                    model_name,
                    field,
                    self.to_state,
                )
                # Depend on our own model being created
                dependencies.append(
                    OperationDependency(
                        app_label, model_name, None, OperationDependency.Type.CREATE
                    )
                )
                # Make operation
                self.add_operation(
                    app_label,
                    operations.AddField(
                        model_name=model_name,
                        name=name,
                        field=field,
                    ),
                    dependencies=list(set(dependencies)),
                )
            # Generate other opns
            if order_with_respect_to:
                self.add_operation(
                    app_label,
                    operations.AlterOrderWithRespectTo(
                        name=model_name,
                        order_with_respect_to=order_with_respect_to,
                    ),
                    dependencies=[
                        OperationDependency(
                            app_label,
                            model_name,
                            order_with_respect_to,
                            OperationDependency.Type.CREATE,
                        ),
                        OperationDependency(
                            app_label, model_name, None, OperationDependency.Type.CREATE
                        ),
                    ],
                )
            related_dependencies = [
                OperationDependency(
                    app_label, model_name, name, OperationDependency.Type.CREATE
                )
                for name in sorted(related_fields)
            ]
            related_dependencies.append(
                OperationDependency(
                    app_label, model_name, None, OperationDependency.Type.CREATE
                )
            )
            for index in indexes:
                self.add_operation(
                    app_label,
                    operations.AddIndex(
                        model_name=model_name,
                        index=index,
                    ),
                    dependencies=related_dependencies,
                )
            for constraint in constraints:
                self.add_operation(
                    app_label,
                    operations.AddConstraint(
                        model_name=model_name,
                        constraint=constraint,
                    ),
                    dependencies=related_dependencies,
                )
            if unique_together:
                self.add_operation(
                    app_label,
                    operations.AlterUniqueTogether(
                        name=model_name,
                        unique_together=unique_together,
                    ),
                    dependencies=related_dependencies,
                )
            # Fix relationships if the model changed from a proxy model to a
            # concrete model.
            relations = self.to_state.relations
            if (app_label, model_name) in self.old_proxy_keys:
                for related_model_key, related_fields in relations[
                    app_label, model_name
                ].items():
                    related_model_state = self.to_state.models[related_model_key]
                    for related_field_name, related_field in related_fields.items():
                        self.add_operation(
                            related_model_state.app_label,
                            operations.AlterField(
                                model_name=related_model_state.name,
                                name=related_field_name,
                                field=related_field,
                            ),
                            dependencies=[
                                OperationDependency(
                                    app_label,
                                    model_name,
                                    None,
                                    OperationDependency.Type.CREATE,
                                )
                            ],
                        )