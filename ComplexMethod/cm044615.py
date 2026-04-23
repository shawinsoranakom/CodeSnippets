def _traverse(obj: Any, root: bool = False, depth: int = 0) -> Node:
        """Walk the object depth first."""

        obj_id = id(obj)
        if obj_id in visited_ids:
            # Recursion detected
            return Node(value_repr="...")

        obj_type = type(obj)
        children: List[Node]
        reached_max_depth = max_depth is not None and depth >= max_depth

        def iter_rich_args(rich_args: Any) -> Iterable[Union[Any, Tuple[str, Any]]]:
            for arg in rich_args:
                if _safe_isinstance(arg, tuple):
                    if len(arg) == 3:
                        key, child, default = arg
                        if default == child:
                            continue
                        yield key, child
                    elif len(arg) == 2:
                        key, child = arg
                        yield key, child
                    elif len(arg) == 1:
                        yield arg[0]
                else:
                    yield arg

        try:
            fake_attributes = hasattr(
                obj, "awehoi234_wdfjwljet234_234wdfoijsdfmmnxpi492"
            )
        except Exception:
            fake_attributes = False

        rich_repr_result: Optional[RichReprResult] = None
        if not fake_attributes:
            try:
                if hasattr(obj, "__rich_repr__") and not isclass(obj):
                    rich_repr_result = obj.__rich_repr__()
            except Exception:
                pass

        if rich_repr_result is not None:
            push_visited(obj_id)
            angular = getattr(obj.__rich_repr__, "angular", False)
            args = list(iter_rich_args(rich_repr_result))
            class_name = obj.__class__.__name__

            if args:
                children = []
                append = children.append

                if reached_max_depth:
                    if angular:
                        node = Node(value_repr=f"<{class_name}...>")
                    else:
                        node = Node(value_repr=f"{class_name}(...)")
                else:
                    if angular:
                        node = Node(
                            open_brace=f"<{class_name} ",
                            close_brace=">",
                            children=children,
                            last=root,
                            separator=" ",
                        )
                    else:
                        node = Node(
                            open_brace=f"{class_name}(",
                            close_brace=")",
                            children=children,
                            last=root,
                        )
                    for last, arg in loop_last(args):
                        if _safe_isinstance(arg, tuple):
                            key, child = arg
                            child_node = _traverse(child, depth=depth + 1)
                            child_node.last = last
                            child_node.key_repr = key
                            child_node.key_separator = "="
                            append(child_node)
                        else:
                            child_node = _traverse(arg, depth=depth + 1)
                            child_node.last = last
                            append(child_node)
            else:
                node = Node(
                    value_repr=f"<{class_name}>" if angular else f"{class_name}()",
                    children=[],
                    last=root,
                )
            pop_visited(obj_id)
        elif _is_attr_object(obj) and not fake_attributes:
            push_visited(obj_id)
            children = []
            append = children.append

            attr_fields = _get_attr_fields(obj)
            if attr_fields:
                if reached_max_depth:
                    node = Node(value_repr=f"{obj.__class__.__name__}(...)")
                else:
                    node = Node(
                        open_brace=f"{obj.__class__.__name__}(",
                        close_brace=")",
                        children=children,
                        last=root,
                    )

                    def iter_attrs() -> (
                        Iterable[Tuple[str, Any, Optional[Callable[[Any], str]]]]
                    ):
                        """Iterate over attr fields and values."""
                        for attr in attr_fields:
                            if attr.repr:
                                try:
                                    value = getattr(obj, attr.name)
                                except Exception as error:
                                    # Can happen, albeit rarely
                                    yield (attr.name, error, None)
                                else:
                                    yield (
                                        attr.name,
                                        value,
                                        attr.repr if callable(attr.repr) else None,
                                    )

                    for last, (name, value, repr_callable) in loop_last(iter_attrs()):
                        if repr_callable:
                            child_node = Node(value_repr=str(repr_callable(value)))
                        else:
                            child_node = _traverse(value, depth=depth + 1)
                        child_node.last = last
                        child_node.key_repr = name
                        child_node.key_separator = "="
                        append(child_node)
            else:
                node = Node(
                    value_repr=f"{obj.__class__.__name__}()", children=[], last=root
                )
            pop_visited(obj_id)
        elif (
            is_dataclass(obj)
            and not _safe_isinstance(obj, type)
            and not fake_attributes
            and _is_dataclass_repr(obj)
        ):
            push_visited(obj_id)
            children = []
            append = children.append
            if reached_max_depth:
                node = Node(value_repr=f"{obj.__class__.__name__}(...)")
            else:
                node = Node(
                    open_brace=f"{obj.__class__.__name__}(",
                    close_brace=")",
                    children=children,
                    last=root,
                    empty=f"{obj.__class__.__name__}()",
                )

                for last, field in loop_last(
                    field
                    for field in fields(obj)
                    if field.repr and hasattr(obj, field.name)
                ):
                    child_node = _traverse(getattr(obj, field.name), depth=depth + 1)
                    child_node.key_repr = field.name
                    child_node.last = last
                    child_node.key_separator = "="
                    append(child_node)

            pop_visited(obj_id)
        elif _is_namedtuple(obj) and _has_default_namedtuple_repr(obj):
            push_visited(obj_id)
            class_name = obj.__class__.__name__
            if reached_max_depth:
                # If we've reached the max depth, we still show the class name, but not its contents
                node = Node(
                    value_repr=f"{class_name}(...)",
                )
            else:
                children = []
                append = children.append
                node = Node(
                    open_brace=f"{class_name}(",
                    close_brace=")",
                    children=children,
                    empty=f"{class_name}()",
                )
                for last, (key, value) in loop_last(obj._asdict().items()):
                    child_node = _traverse(value, depth=depth + 1)
                    child_node.key_repr = key
                    child_node.last = last
                    child_node.key_separator = "="
                    append(child_node)
            pop_visited(obj_id)
        elif _safe_isinstance(obj, _CONTAINERS):
            for container_type in _CONTAINERS:
                if _safe_isinstance(obj, container_type):
                    obj_type = container_type
                    break

            push_visited(obj_id)

            open_brace, close_brace, empty = _BRACES[obj_type](obj)

            if reached_max_depth:
                node = Node(value_repr=f"{open_brace}...{close_brace}")
            elif obj_type.__repr__ != type(obj).__repr__:
                node = Node(value_repr=to_repr(obj), last=root)
            elif obj:
                children = []
                node = Node(
                    open_brace=open_brace,
                    close_brace=close_brace,
                    children=children,
                    last=root,
                )
                append = children.append
                num_items = len(obj)
                last_item_index = num_items - 1

                if _safe_isinstance(obj, _MAPPING_CONTAINERS):
                    iter_items = iter(obj.items())
                    if max_length is not None:
                        iter_items = islice(iter_items, max_length)
                    for index, (key, child) in enumerate(iter_items):
                        child_node = _traverse(child, depth=depth + 1)
                        child_node.key_repr = to_repr(key)
                        child_node.last = index == last_item_index
                        append(child_node)
                else:
                    iter_values = iter(obj)
                    if max_length is not None:
                        iter_values = islice(iter_values, max_length)
                    for index, child in enumerate(iter_values):
                        child_node = _traverse(child, depth=depth + 1)
                        child_node.last = index == last_item_index
                        append(child_node)
                if max_length is not None and num_items > max_length:
                    append(Node(value_repr=f"... +{num_items - max_length}", last=True))
            else:
                node = Node(empty=empty, children=[], last=root)

            pop_visited(obj_id)
        else:
            node = Node(value_repr=to_repr(obj), last=root)
        node.is_tuple = type(obj) == tuple
        node.is_namedtuple = _is_namedtuple(obj)
        return node