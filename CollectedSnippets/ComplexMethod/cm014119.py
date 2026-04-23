def wrap_literal(self, value: object) -> VariableTracker:
        if type(value) is int:
            assert isinstance(value, int)
            # allowlist has higher precedence over specialization control.
            if is_dynamic_source(self.source.name):
                log.debug("%s marked dynamic via source whitelist", self.source.name)
                return self.wrap_symint(value, dynamism=DimDynamic.DYNAMIC)

            if is_unbacked_source(self.source.name):
                log.debug("%s marked unbacked via source whitelist", self.source.name)
                return self.wrap_symint(value, dynamism=DimDynamic.UNBACKED)

            if not config.specialize_int:
                # unspecializing int by default, but still
                # specialize for the following conditions
                if is_int_specialization_case(value, self.source):
                    recompile_hint = None
                    if (
                        self.source.guard_source.is_unspecialized_builtin_nn_module()
                        or self.source.guard_source.is_unspecialized_nn_module()
                    ):
                        # This means that it is an integer from a NN module.
                        # Dynamo considers nn module int attributes to be static
                        # (a good heuristic). But a user might want to mark the
                        # int attribute to be a symint, so track this integer
                        # for recompilation later.
                        recompile_hint = (
                            "torch.compile considers integer attributes of the nn.Module to be static. "
                            "If you are observing recompilation, you might want to make this integer dynamic "
                            "using torch._dynamo.config.allow_unspec_int_on_nn_module = True, or convert this "
                            "integer into a tensor."
                        )

                    process_automatic_dynamic(
                        self.tx,
                        self.source.name,
                        FrameStateSizeEntry.make_scalar(value),
                        is_unspecialized_nn_module=self.source.guard_source.is_unspecialized_nn_module(),
                    )
                    self.install_guards(
                        functools.partial(
                            GuardBuilder.EQUALS_MATCH, recompile_hint=recompile_hint
                        )
                    )
                    return ConstantVariable.create(value=value, source=self.source)

                return self._wrap_lazy_constant(value, self._wrap_symint_for_lazy)

            return self._wrap_lazy_constant(value)
        elif type(value) is float:
            assert isinstance(value, float)
            if not config.specialize_float:
                return self._wrap_lazy_constant(value, self._wrap_symfloat_for_lazy)

            return self._wrap_lazy_constant(value)
        elif type(value) in (bool, str):
            assert isinstance(value, (bool, str))
            return self._wrap_lazy_constant(value)
        else:
            self.install_guards(GuardBuilder.CONSTANT_MATCH)
            result = ConstantVariable.create(value=value, source=self.source)
            if isinstance(value, (list, set)):
                return self.tx.output.side_effects.track_mutable(value, result)
            return result