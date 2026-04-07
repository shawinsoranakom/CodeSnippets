def _resolve_dependency(dependency):
        """
        Return the resolved dependency and a boolean denoting whether or not
        it was swappable.
        """
        if dependency.app_label != "__setting__":
            return dependency, False
        resolved_app_label, resolved_object_name = getattr(
            settings, dependency.model_name
        ).split(".")
        return (
            OperationDependency(
                resolved_app_label,
                resolved_object_name.lower(),
                dependency.field_name,
                dependency.type,
            ),
            True,
        )