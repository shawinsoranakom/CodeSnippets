def signature(
        self,
        *,
        strip_default: bool = False,
        strip_view_copy_name: bool = False,
        keep_return_names: bool = False,
    ) -> FunctionSchema:
        """
                Certain schemas are 'related', in that they are simply
                inplace/out/functional versions of the same function.  This method
                factors these schemas into the "core" functional signature which
                is equal across all versions.

                Here is what normalization happens to the schema to convert
                it to a signature:
                - The overload name is stripped (name is retained, since
                  it expresses semantic content about what the function does)
                - Inplace is set False
                - Out arguments are stripped
                - Mutable post_self_positional args are converted to returns
                - Mutability annotations are stripped  (this is sound
                  because you cannot overload on mutability annotation)
                - Return names are stripped since they are not overloadable and
                  some variants have return names but some not
                - TensorOptions are dropped
                  because out= variants of factory functions don't include them
                  (and we want to be able to pair up factory functions with their out variants)

                Finally, we want to be able to pair up related "view" and their
                corresponding "view_copy" operators. We do this by optionally
                stripping the trailing "_copy" from the base name.

                Example of a mutable op before and after:

                f.func (Mutable operator):
        _fused_moving_avg_obs_fq_helper(Tensor self, Tensor observer_on, Tensor fake_quant_on, Tensor(a!) running_min, Tensor(b!) running_max, Tensor(c!) scale, Tensor(d!) zero_point, float averaging_const, int quant_min, int quant_max, int ch_axis, bool per_row_fake_quant=False, bool symmetric_quant=False) -> (Tensor output, Tensor mask)  # noqa: B950

                f.func (Corresponding functional operator):
        _fused_moving_avg_obs_fq_helper.functional(Tensor self, Tensor observer_on, Tensor fake_quant_on, Tensor running_min, Tensor running_max, Tensor scale, Tensor zero_point, float averaging_const, int quant_min, int quant_max, int ch_axis, bool per_row_fake_quant=False, bool symmetric_quant=False) -> (Tensor output, Tensor mask, Tensor running_min_out, Tensor running_max_out, Tensor scale_out, Tensor zero_point_out)  # noqa: B950

                f.func.signature() output:
        _fused_moving_avg_obs_fq_helper(Tensor self, Tensor observer_on, Tensor fake_quant_on, Tensor running_min, Tensor running_max, Tensor scale, Tensor zero_point, float averaging_const, int quant_min, int quant_max, int ch_axis, bool per_row_fake_quant=False, bool symmetric_quant=False) -> (Tensor, Tensor, Tensor, Tensor, Tensor, Tensor)  # noqa: B950
        """

        def strip_ret_annotation(r: Return) -> Return:
            return Return(
                name=r.name if keep_return_names else None,
                type=r.type,
                annotation=None,
            )

        base_name = self.name.name.base
        if strip_view_copy_name:
            if base_name.endswith("_copy"):
                base_name = base_name.replace("_copy", "")
            elif base_name.endswith("_scatter"):
                base_name = base_name.replace("scatter", "inverse")

        # find mutable inputs that are not originally returned, and convert them to returns
        returns_from_mutable_inputs = tuple(
            # When we're grouping functions we strip the return names,
            # but when we're generating the actual functional variants then we follow
            # a convention for what to name the returns
            Return(
                name=f"{a.name}_out" if keep_return_names else None,
                type=a.type,
                annotation=None,
            )
            for a in itertools.chain(
                # Order is important here (otherwise e.g. inplace with mutable args
                # and out= with mutable args won't have the same signature)
                (
                    [self.arguments.self_arg.argument]
                    if self.arguments.self_arg is not None
                    else []
                ),
                self.arguments.out,
                self.arguments.post_self_positional,
            )
            if a.annotation is not None
            and a.annotation.is_write
            and not any(a.annotation == r.annotation for r in self.returns)
        )
        original_returns = tuple(map(strip_ret_annotation, self.returns))
        # Ordering is important here. We expect the "mutable input" returns to come last.
        returns = original_returns + returns_from_mutable_inputs

        args_sig = self.arguments.signature(strip_default=strip_default)
        # See Note [bernoulli.p schema]
        if str(self.name) == "bernoulli.p":
            args_sig = Arguments.parse(str(args_sig).replace("float p", "float p=0.5"))

        return FunctionSchema(
            name=OperatorName(
                name=BaseOperatorName(
                    base=base_name,
                    inplace=False,
                    dunder_method=self.name.name.dunder_method,
                ),
                overload_name="",  # stripped
            ),
            arguments=args_sig,
            returns=returns,
        )