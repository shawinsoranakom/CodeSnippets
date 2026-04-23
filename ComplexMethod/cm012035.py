def call_function(self, target: Callable, args: Any, kwargs: dict[str, Any]) -> Any:  # type: ignore[type-arg]
        if target is operator.getitem and isinstance(args[0], (list, tuple, dict)):
            return super().call_function(target, args, kwargs)

        # hasattr on OpOverloadPacket is slow, check isinstance first
        if not isinstance(target, torch._ops.OpOverloadPacket) and hasattr(
            target, "_inductor_lowering_function"
        ):
            # passthrough lowerings from .pattern_matcher
            return target(*args, **kwargs)

        if target not in lowerings:
            assert isinstance(target, torch._ops.OpOverload), (
                f"{target} is not an OpOverload"
            )
            base_name = target.name().split(".")[0]
            if base_name in FALLBACK_ALLOW_LIST:
                make_fallback(
                    target,
                    warn=False,
                    get_decomp_fn=self.get_decomp_fn,
                    override_decomp=True,
                )
            elif config.implicit_fallbacks:
                error = (
                    MissingOperatorWithDecomp
                    if get_decompositions([target])
                    else MissingOperatorWithoutDecomp
                )
                log.info(
                    "Creating implicit fallback for:\n%s",
                    error.operator_str(target, args, kwargs),
                )

                tag: torch._C.Tag | None = get_layout_constraint_tag(
                    target, with_default=False
                )
                if (
                    tag is None
                    and torch._library.utils.is_builtin(target)
                    and self.is_backward
                ):
                    # for implicit fallback ATen ops during backward, if there
                    # is no layout constraint tag, we conservatively require contiguous
                    # input since some eager kernels do not
                    # support non-contiguous inputs. Otherwise they may silently cause
                    # accuracy problems. Check https://github.com/pytorch/pytorch/issues/140452
                    # We only do this For ATen ops and for backward.
                    #
                    # TODO: should really switch to "needs_fixed_stride" constraint on these
                    # and identify them one by one.
                    decided_constraint: Callable[..., tuple[Any, Any]] | None = (
                        require_contiguous
                    )
                else:
                    default_tag: torch._C.Tag = get_layout_constraint_tag(
                        target, with_default=True
                    )
                    decided_constraint = tag_to_layout_constraint(default_tag)

                make_fallback(
                    target,
                    layout_constraint=decided_constraint,
                    get_decomp_fn=self.get_decomp_fn,
                )

            elif get_decompositions([target]):
                # There isn't a good way to dynamically patch this in
                # since AOT Autograd already ran.  The error message tells
                # the user how to fix it.
                raise MissingOperatorWithDecomp(target, args, kwargs)
            else:
                raise MissingOperatorWithoutDecomp(target, args, kwargs)

        try:
            log.debug("  via %s", lowerings[target])  # type: ignore[index]

            n = self.current_node
            layout_constraints = maybe_layout_constraints(target)
            if layout_constraints:
                old_args, old_kwargs = args, kwargs
                if layout_constraints is constrain_to_fake_tensors:
                    # only constrain_to_fake_tensor if this exists.
                    # otherwise, no constraints at all: the implication is
                    # that this operator was inserted by a custom pass
                    # so we'll give them the freedom.
                    if "eager_input_vals" in n.meta:
                        fake_args, fake_kwargs = n.meta["eager_input_vals"]

                        # (fake_args, fake_kwargs) might not align with (args, kwargs).
                        # we need to normalize them based on the schema
                        assert isinstance(target, torch._ops.OpOverload)

                        def normalize(args: Any, kwargs: Any) -> tuple[Any, Any]:
                            result = torch.fx.operator_schemas.normalize_function(
                                target, args, kwargs
                            )
                            assert result is not None
                            return result[0], result[1]

                        fake_args, fake_kwargs = normalize(fake_args, fake_kwargs)
                        args, kwargs = normalize(args, kwargs)
                        old_args, old_kwargs = normalize(old_args, old_kwargs)

                        args, kwargs = constrain_to_fake_tensors(
                            args, kwargs, fake_args, fake_kwargs
                        )
                else:
                    args, kwargs = layout_constraints(n, *args, **kwargs)

            if "should_fallback" in n.meta:
                out = fallback_handler(target, add_to_fallback_set=False)(
                    *args, **kwargs
                )
            else:
                out = None

                if (
                    target in user_lowerings
                    and target not in V.active_user_lowering_ops
                ):
                    # User-registered lowering takes priority, with recursion guard
                    V.active_user_lowering_ops.add(target)
                    try:
                        # pyrefly: ignore[bad-index]
                        out = user_lowerings[target](*args, **kwargs)
                    finally:
                        V.active_user_lowering_ops.discard(target)

                # If no user_lowering, or it returned None fall back to normal lowering
                if out is None:
                    if target in lowerings:
                        out = lowerings[target](*args, **kwargs)
                    else:
                        # Fallback for ops not in lowerings (e.g., custom ops during recursion)
                        out = fallback_handler(target, add_to_fallback_set=False)(
                            *args, **kwargs
                        )

            if layout_constraints:
                # layout_constraints are allowed to make new copies of the inputs.
                # if they do, and if the target is mutable, then we need to
                # write the new values back into the original inputs.
                self.propagate_mutation(n, old_args, old_kwargs, args, kwargs)  # type: ignore[possibly-undefined]

            return out
        except Exception as e:
            stack_trace = None
            if (
                hasattr(self, "current_node")
                and self.current_node is not None
                and hasattr(self.current_node, "meta")
                and self.current_node.meta is not None
            ):
                stack_trace = self.current_node.meta.get("stack_trace", None)
            raise LoweringException(
                e, target, args, kwargs, stack_trace=stack_trace
            ).with_traceback(e.__traceback__) from None