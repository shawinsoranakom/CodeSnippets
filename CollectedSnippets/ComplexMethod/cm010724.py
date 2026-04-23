def resolve_names_to_kernels(
            names: list[str],
            namespace: dict[str, Any],
            assignments: dict[str, list[ast.expr]] | None = None,
            visited: set[str] | None = None,
        ) -> list[object]:
            """
            Resolve a list of names to triton kernels using the given namespace.
            """
            if visited is None:
                visited = set()

            results: list[object] = []
            for name in names:
                if name in visited:
                    continue
                visited.add(name)

                if name in namespace:
                    obj = namespace[name]
                    kernel = resolve_to_kernel(obj)
                    if kernel is not None:
                        results.append(kernel)
                        continue
                    # recurse into callable objects (factory fn's),
                    # unwrapping decorators if applicable
                    if callable(obj):
                        try:
                            unwrapped = inspect.unwrap(obj)
                        except ValueError:
                            unwrapped = obj
                        if hasattr(unwrapped, "__code__"):
                            nested = find_triton_kernels(
                                unwrapped, visited_fns, depth + 1
                            )
                            if nested:
                                results.extend(nested)
                                continue
                    logger.debug("failed to resolve %s to a triton kernel", name)
                elif assignments is not None and name in assignments:
                    # trace through local assignments
                    for rhs_expr in assignments[name]:
                        referenced = extract_names_from_expr(rhs_expr)
                        traced = resolve_names_to_kernels(
                            referenced, namespace, assignments, visited
                        )
                        results.extend(traced)
                else:
                    logger.debug("%s not found in namespace or assignments", name)

            return results