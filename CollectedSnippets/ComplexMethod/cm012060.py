def run_node(self, node: torch.fx.Node) -> Any:
        if node.target == "output":
            # because we remove nodes from env on last non output use,
            # re-define them now or we'll get error in interpreter
            def set_env(arg: torch.fx.Node) -> None:
                self.env[arg] = self.unknown_value

            # In-place is fine since we don't mutate
            pytree.tree_map_only_(torch.fx.Node, set_env, node.args)
            return super().run_node(node)

        args, kwargs = self.fetch_args_kwargs_from_env(node)
        flattened_inputs = pytree.arg_tree_leaves(*args, **kwargs)

        # We need to do this weird thing because in cases where flattened_inputs
        # contains a ScriptObject, equality checking results in a type error if
        # the types are different.
        if any(
            type(self.unknown_value) is type(input_) and self.unknown_value == input_
            for input_ in flattened_inputs
        ):
            return self.unknown_value

        # TODO - fix errors with this
        if (
            node.op == "call_function"
            and node.target is aten._efficientzerotensor.default
        ):
            return self.unknown_value

        # TODO - constant folding triton kernel returns the inputs -- fix this
        if (
            node.op == "call_function"
            and node.name == "triton_kernel_wrapper_functional_proxy"
        ):
            return self.unknown_value

        # skip constructors, since inductor generates optimal code for them already
        # and turning into tensor would result in an additional global memory read
        # TODO - more complicated strategy
        if (
            self.skip_constructors
            and not is_const_source(node, self.lifted_constant_names)
            and not any(isinstance(e, torch.Tensor) for e in flattened_inputs)
        ):
            return self.unknown_value

        # All mutations should either be removed or on inputs which we did not make constant
        if (
            isinstance(node.target, torch._ops.OpOverload)
            and torch.Tag.nondeterministic_seeded in node.target.tags
        ):
            return self.unknown_value

        if node.op == "call_function" and isinstance(
            node.target, torch._ops.HigherOrderOperator
        ):
            return self.unknown_value

        out = self._deduce_value(node)

        if isinstance(
            out,
            (
                torch._C.ScriptObject,
                torch._library.fake_class_registry.FakeScriptObject,
            ),
        ):
            return out

        if out is self.unknown_value:
            return self.unknown_value

        if not is_const_source(node, self.lifted_constant_names) and (
            isinstance(out, torch.Tensor) or out is self.deferred_value
        ):
            if (
                out is not self.deferred_value
                and out.device.type == "meta"  # pyrefly: ignore[missing-attribute]
            ):
                return out

            if not self.insertable_tensor_check(
                out  # pyrefly: ignore[bad-argument-type]
            ):
                return out

            if self.is_impure(node):
                return self.unknown_value

            self.add_node_replacement(node, out)  # pyrefly: ignore[bad-argument-type]

            flattened_node_inps = pytree.arg_tree_leaves(*node.args, **node.kwargs)

            for n in flattened_node_inps:
                if not isinstance(n, torch.fx.Node):
                    continue

                self.replaced_uses[n] += 1

            for to_delete in self.user_to_last_uses.get(node, []):
                if self.replaced_uses[to_delete] == len(to_delete.users):
                    self.node_replacements.pop(to_delete, None)

        return out