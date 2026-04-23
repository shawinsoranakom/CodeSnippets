def remove_unused_graphargs(self) -> None:
        # NB: It's OK to drop GraphArg for symbols that ended up being
        # specialized iff they are not used in runtime assertions.  You don't
        # even have to make a guard for it, because ShapeEnv produce_guards
        # operates on tracked_fakes, which never gets pruned.
        # That being said, you'll get marginally better generated
        # guard code if you promote the guard into a Dynamo guard (since that
        # allows for the guard to be done using C++ guards.)  If we get
        # ShapeEnv guards to go into C++ guards, this will stop being a thing
        # though!

        assert self.should_exit

        # Miniature DCE pass, but only for obviously trivial operations
        def is_static_true(b_node: fx.node.Argument) -> bool:
            if b_node is True:
                return True
            if not isinstance(b_node, fx.Node):
                return False
            b = b_node.meta.get("example_value")
            if b is None:
                return False
            if b is True:
                return True
            if (
                isinstance(b, torch.SymBool)
                and (r := b.node.maybe_as_bool()) is not None
            ):
                return r
            # TODO: We can also technically remove all cases when the input
            # doesn't have unbacked inputs, since it's all in the ShapeEnv
            return False

        def is_symnode_arg(a: fx.node.Argument) -> bool:
            from torch.fx.experimental.sym_node import SymTypes

            if isinstance(a, (int, float, bool)):
                return True
            if isinstance(a, fx.Node):
                return isinstance(a.meta.get("example_value"), SymTypes)
            return False

        # NB: We assume that you cannot do mutations on int/float/bool,
        # because they are immutable types, and therefore is always safe to
        # DCE.
        def is_symnode_compute_node(node: fx.Node) -> bool:
            from torch.fx.experimental.sym_node import SymTypes

            if node.op != "call_function":
                return False
            # TODO: I don't think it's possible to have a bare int/float here?
            if not isinstance(node.meta.get("example_value"), SymTypes):
                return False
            # TODO: This will bail here if you ever end up with a more complicated
            # computation function, like sum(list_of_ints), even though it
            # should be DCE'able
            if not all(is_symnode_arg(a) for a in node.args):
                return False
            if not all(is_symnode_arg(a) for a in node.kwargs.values()):
                return False
            return True

        from torch.fx.experimental.symbolic_shapes import is_accessor_node

        for node in reversed(list(self.graph.nodes)):
            if len(list(node.users)) == 0:
                if (
                    node.op == "get_attr"
                    or (node.op == "call_function" and node.target is operator.getitem)
                    or (
                        node.op == "call_function"
                        and node.target is torch._check
                        and is_static_true(node.args[0])
                    )
                    or is_symnode_compute_node(node)
                    or is_accessor_node(node)
                ):
                    self.remove_node(node)

        def placeholder_binds_symbol(node: fx.Node) -> sympy.Symbol | None:
            arg = node.meta["grapharg"]
            example = arg.example
            if isinstance(example, torch.SymInt) and isinstance(
                example.node.expr, sympy.Symbol
            ):
                return example.node.expr
            return None

        def remove_unused(node: fx.Node) -> None:
            log.debug("REMOVE UNUSED GRAPHARG %s", node.meta["grapharg"].source.name)
            # I'm not really sure why you need to delete these from the
            # node since the node is going to get removed
            del node.meta["grapharg"]
            self.remove_node(node)
            self.real_value_cache.pop(node, None)

        used_symbols: set[sympy.Symbol] = set()

        def update_used_symbols(
            used_symbols: set[sympy.Symbol], fake: torch.SymInt | torch.Tensor
        ) -> None:
            used_symbols |= free_symbols(fake)

        recheck_placeholders = []
        for node in self.placeholders:
            binds_symbol = placeholder_binds_symbol(node) is not None
            # Don't delete symbol bindings yet
            if binds_symbol:
                if not node.users:
                    recheck_placeholders.append(node)
            else:
                if not node.users and not isinstance(
                    node.meta["grapharg"], BackwardStateGraphArg
                ):
                    remove_unused(node)
                else:
                    # Register the free symbols as uses
                    arg = node.meta["grapharg"]
                    if isinstance(arg, BackwardStateGraphArg):
                        continue
                    if isinstance(node.meta["grapharg"].example, torch.ScriptObject):
                        real_script_obj = node.meta["grapharg"].example
                        fake_script_obj = node.meta["grapharg"].example_strong_ref
                        if not torch._library.fake_class_registry.tracing_with_real(
                            real_script_obj
                        ):
                            flat_dict = dict(real_script_obj.__obj_flatten__())  # type: ignore[attr-defined]
                            for attr in flat_dict:
                                fake_attr_val = getattr(
                                    fake_script_obj.wrapped_obj, attr
                                )
                                pytree.tree_map_only(
                                    (torch.SymInt, torch.Tensor),
                                    lambda t: update_used_symbols(used_symbols, t),
                                    fake_attr_val,
                                )
                        continue
                    if is_opaque_type(type(node.meta["grapharg"].example)):
                        continue
                    fake = (
                        arg.fake_tensor if arg.fake_tensor is not None else arg.example
                    )
                    update_used_symbols(used_symbols, fake)

        # After removing unused graphargs, prune unused binds_symbol
        for node in recheck_placeholders:
            symbol = placeholder_binds_symbol(node)
            if symbol is not None:
                if symbol not in used_symbols:
                    remove_unused(node)
                else:
                    # Make sure we delete later occurrences of the same symbol
                    used_symbols.remove(symbol)