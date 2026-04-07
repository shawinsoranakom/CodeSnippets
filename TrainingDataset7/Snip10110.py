def _get_dependencies_for_foreign_key(app_label, model_name, field, project_state):
        remote_field_model = None
        if hasattr(field.remote_field, "model"):
            remote_field_model = field.remote_field.model
        else:
            relations = project_state.relations[app_label, model_name]
            for (remote_app_label, remote_model_name), fields in relations.items():
                if any(
                    field == related_field.remote_field
                    for related_field in fields.values()
                ):
                    remote_field_model = f"{remote_app_label}.{remote_model_name}"
                    break
        # Account for FKs to swappable models
        swappable_setting = getattr(field, "swappable_setting", None)
        if swappable_setting is not None:
            dep_app_label = "__setting__"
            dep_object_name = swappable_setting
        else:
            dep_app_label, dep_object_name = resolve_relation(
                remote_field_model,
                app_label,
                model_name,
            )
        dependencies = [
            OperationDependency(
                dep_app_label, dep_object_name, None, OperationDependency.Type.CREATE
            )
        ]
        if getattr(field.remote_field, "through", None):
            through_app_label, through_object_name = resolve_relation(
                field.remote_field.through,
                app_label,
                model_name,
            )
            dependencies.append(
                OperationDependency(
                    through_app_label,
                    through_object_name,
                    None,
                    OperationDependency.Type.CREATE,
                )
            )
        return dependencies