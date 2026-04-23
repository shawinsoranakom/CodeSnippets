def create_node(
        self,
        kind: str,
        target: Target,
        args: tuple[Argument, ...],
        kwargs: dict[str, Argument],
        name: str | None = None,
        type_expr: Any | None = None,
    ) -> Node:
        """
        Inserts a graph node given target, args, kwargs, and name.

        This method can be overridden to do extra checking, validation, or
        modification of values used in node creation. For example, one might
        want to disallow in-place operations from being recorded.
        """

        if kind == "call_function" and self.check_mutable_operations:
            target_fn = cast(Callable[..., Any], target)
            check_for_mutable_operation(target_fn, args, kwargs)

        node = self.graph.create_node(kind, target, args, kwargs, name, type_expr)
        # TODO node_name_to_scope will be depreciated in favor of
        # node.meta['nn_module_stack']
        self.node_name_to_scope[node.name] = (
            self.scope.module_path,
            self.scope.module_type,
        )

        # Optionally set stack trace on the created Node for debugging purposes
        if fx_traceback.has_preserved_node_meta():
            current_meta: dict[str, Any] = fx_traceback.get_current_meta()

            stack_trace = current_meta.get("stack_trace")
            if stack_trace:
                node.stack_trace = stack_trace

                if fx_traceback.GRADIENT_ACC_SPECIAL_STACK in stack_trace:
                    node.meta["is_gradient_acc"] = True
                    node.meta["autograd_backward"] = True

            # Explicitly set the stack_trace, nn_module_stack and source_fn on the node.meta
            # If other meta fields are needed, they can be added here
            for field in _COPY_META_FIELDS:
                if field in current_meta:
                    node.meta[field] = copy.copy(current_meta[field])

            new_seq_nr = _get_seq_nr(node.name)
            if new_seq_nr is not None:
                annotation_log.debug(
                    "Assigning new_seq_nr %s to %s", new_seq_nr, node.name
                )
                node.meta["seq_nr"] = new_seq_nr

            # See Note [Functionalization View Replay Annotation]
            # Overriding some node meta with the original node meta of the
            # regenerated node.
            replay_node: Node | None = fx_traceback.get_current_replay_node()
            if replay_node is not None:
                node.meta["is_functional_regenerated"] = True
                if "custom" in replay_node.meta:
                    node.meta["custom"] = replay_node.meta.get("custom")
                if "stack_trace" in replay_node.meta:
                    node.stack_trace = replay_node.meta.get("stack_trace")

            if current_meta.get("autograd_backward", False):
                node.meta["autograd_backward"] = True

        elif self.module_stack:
            node.meta["nn_module_stack"] = copy.copy(self.module_stack)

        if self.record_stack_traces and not node.stack_trace:
            user_stack_summary = CapturedTraceback.extract().summary()
            if user_stack_summary:
                user_stack_summary = self._filter_traceback_frames(user_stack_summary)
                if user_stack_summary:
                    node.stack_trace = "".join(user_stack_summary.format()).strip()

        log.debug("create_node %s", node)
        return node