def create_node(
        self,
        op: str,
        target: Target,
        args: tuple[Argument, ...] | None = None,
        kwargs: dict[str, Argument] | None = None,
        name: str | None = None,
        type_expr: Any | None = None,
    ) -> Node:
        """
        Create a ``Node`` and add it to the ``Graph`` at the current insert-point.
        Note that the current insert-point can be set via :meth:`Graph.inserting_before`
        and :meth:`Graph.inserting_after`.

        Args:
            op (str): the opcode for this Node. One of 'call_function', 'call_method', 'get_attr',
                'call_module', 'placeholder', or 'output'. The semantics of these opcodes are
                described in the ``Graph`` docstring.

            args (Optional[Tuple[Argument, ...]]): is a tuple of arguments to this node.

            kwargs (Optional[Dict[str, Argument]]): the kwargs of this Node

            name (Optional[str]): an optional string name for the ``Node``.
                This will influence the name of the value assigned to in the
                Python generated code.

            type_expr (Optional[Any]): an optional type annotation representing the
                Python type the output of this node will have.

        Returns:

            The newly-created and inserted node.
        """
        # `target in _legal_ops` is checked in Node.__init__
        if not args:
            args = ()
        else:
            if not isinstance(args, tuple):
                raise AssertionError(f"args must be a tuple, got {type(args)}")
        if not kwargs:
            kwargs = immutable_dict()
        else:
            if not isinstance(kwargs, dict):
                raise AssertionError(f"kwargs must be a dict, got {type(kwargs)}")

        candidate = name if name is not None else self._target_to_str(target)
        name = self._graph_namespace.create_name(candidate, None)
        n = Node(self, name, op, target, args, kwargs, type_expr)

        if (
            self.owning_module is not None
            and getattr(self.owning_module, "_create_node_hooks", None) is not None
        ):
            for f in self.owning_module._create_node_hooks:
                f(n)

        self._graph_namespace.associate_name_with_obj(name, n)

        self._insert(n)
        self._find_nodes_lookup_table.insert(n)
        self._len += 1
        return n