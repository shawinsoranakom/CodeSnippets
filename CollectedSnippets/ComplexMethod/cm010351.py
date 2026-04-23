def __init__(self, dependency_graph: DiGraph, debug=False):
        # Group errors by reason.
        broken: dict[PackagingErrorReason, list[str]] = defaultdict(list)
        for module_name, attrs in dependency_graph.nodes.items():
            error = attrs.get("error")
            if error is None:
                continue
            if error == PackagingErrorReason.NO_ACTION:
                if "action" in attrs:
                    raise AssertionError(
                        f"module {module_name} has NO_ACTION error but action is set"
                    )
            broken[error].append(module_name)

        message = io.StringIO()
        message.write("\n")

        for reason, module_names in broken.items():
            message.write(f"* {reason.value}\n")
            for module_name in module_names:
                message.write(f"    {module_name}\n")

                # Print additional context if it's provided.
                error_context = dependency_graph.nodes[module_name].get("error_context")
                if error_context is not None:
                    message.write(f"      Context: {error_context}\n")
                if module_name in _DISALLOWED_MODULES:
                    message.write(
                        "      Note: While we usually use modules in the python standard library "
                        f"from the local environment, `{module_name}` has a lot of system "
                        "level access and therefore can pose a security risk. We heavily "
                        f"recommend removing `{module_name}` from your packaged code. However, if that "
                        "is not possible, add it to the extern list by calling "
                        f'PackageExporter.extern("`{module_name}`")\n'
                    )
                if debug:
                    module_path = dependency_graph.first_path(module_name)
                    message.write(
                        f"      A path to {module_name}: {' -> '.join(module_path)}\n"
                    )
        if not debug:
            message.write("\n")
            message.write(
                "Set debug=True when invoking PackageExporter for a visualization of where "
                "broken modules are coming from!\n"
            )
        # Save the dependency graph so that tooling can get at it.
        self.dependency_graph = dependency_graph
        super().__init__(message.getvalue())