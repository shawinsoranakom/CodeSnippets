def treespec_tuple(
    iterable: Iterable[PyTreeSpec] = (),
    /,
    *,
    none_is_leaf: bool = False,
    namespace: str = "",
) -> PyTreeSpec:
    children = tuple(iterable)
    if any(not _is_pytreespec_instance(child) for child in children):
        raise ValueError(f"Expected a tuple of PyTreeSpecs, got: {children!r}.")
    if any(child.none_is_leaf != none_is_leaf for child in children):
        raise ValueError(
            "All children PyTreeSpecs must have the same `none_is_leaf` value "
            f"as the parent; expected {none_is_leaf}, got: {children!r}.",
        )
    if any(child.namespace not in (namespace, "") for child in children):
        raise ValueError(
            "All children PyTreeSpecs must have the same `namespace` value "
            f"as the parent; expected {namespace!r}, got: {children!r}.",
        )
    handler = optree.register_pytree_node.get(tuple, namespace=namespace)
    assert handler is not None
    return PyTreeSpec(
        tuple(children),
        tuple,
        None,
        tuple(range(len(children))),
        handler.unflatten_func,
        none_is_leaf=none_is_leaf,
        namespace=namespace,
    )