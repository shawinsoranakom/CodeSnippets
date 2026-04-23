def is_fake_tensor_same(new, old, *, node):
            if type(new) is not type(old):
                return False
            if isinstance(new, (list, tuple)):
                if len(new) != len(old):
                    return False
                return all(
                    is_fake_tensor_same(new_i, old_i, node=node)
                    for new_i, old_i in zip(new, old)
                )
            if new is None:
                return old is None
            if not isinstance(new, torch.Tensor):
                assert isinstance(new, (torch.SymInt, torch.SymBool, torch.SymFloat)), (
                    f"Unknown type {type(new)} in {self.graph}"
                )
                return (
                    new.node.shape_env._maybe_evaluate_static(
                        sympy.Eq(new.node.expr, old.node.expr)
                    )
                    == sympy.true
                )
            if not is_intlist_same(new.shape, old.shape) or new.layout != old.layout:
                return False
            if new.layout == torch.strided and (
                not is_intlist_same(new.stride(), old.stride())
                or not statically_known_true(
                    new.storage_offset() == old.storage_offset()
                )
            ):
                return False

            if new.device != old.device:
                return False

            if get_storage(new) == get_storage(old):
                return True

            def any_user_may_alias(node):
                if not isinstance(node.meta["val"], torch.Tensor):
                    # analysis too complicated on lists, can support in the future
                    return True
                for user in node.users:
                    if not (
                        isinstance(
                            user.target,
                            (torch._ops.OpOverload, torch._ops.HigherOrderOperator),
                        )
                        or user.target
                        is torch._inductor.fx_passes.reinplace._generalized_scatter
                    ):
                        return True
                    if isinstance(user.target, torch._ops.HigherOrderOperator):
                        # HOPs that survive until inductor are all non-aliasing HOPs.
                        # We will likely never support HOPs that are aliasing.
                        continue
                    # Strategy: do a FakeTensor prop, see if the storage aliases.
                    # If Inductor ever gets tighter invariants on OpOverloads
                    # (that is, we ban things like torch.ops.aten.reshape calls in the graph),
                    # Then this could just be a fast schema lookup.
                    is_valid, args, kwargs = get_fake_args_kwargs(user)
                    if not is_valid:
                        return True
                    with (
                        V.fake_mode,
                        enable_python_dispatcher(),
                        contextlib.ExitStack() as stack,
                    ):
                        # Ignore unbacked symbols (if they exist): we're making
                        # this FakeTensor and then throwing it away.
                        shape_env = V.fake_mode.shape_env
                        if shape_env is not None:
                            stack.enter_context(
                                shape_env.ignore_fresh_unbacked_symbols()
                            )
                        new_fake_tensor = user.target(*args, **kwargs)
                    if not isinstance(new_fake_tensor, torch.Tensor):
                        # analysis too complicated on lists, can support in the future
                        return True
                    if get_storage(new_fake_tensor) == get_storage(node.meta["val"]):
                        return True
                return False

            # This is the case where it returns a completely fresh storage that's used nowhere else.
            # If the FakeTensor's storage is fresh and none of the node's users can alias it, then
            # we don't need to update this node.
            if (
                existing_storages[get_storage(old)] == 1
                and get_storage(new) not in existing_storages
                and not any_user_may_alias(node)
            ):
                return True

            return False