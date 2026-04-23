def output(
        self,
        target: torch.fx.node.Target,
        args: tuple[torch.fx.node.Argument, ...],
        kwargs: dict[str, object],
    ) -> None:
        result = super().output(target, args, kwargs)  # type: ignore[arg-type]
        if not isinstance(result, (tuple, list)):
            # nested subgraphs can have singleton outputs
            result = (result,)
        assert isinstance(result, (tuple, list)), type(result)
        result = [
            ir.OpaqueValueTypeConstant(value=x) if is_opaque_value_type(type(x)) else x
            for x in result
        ]
        assert all(
            isinstance(
                x,
                (
                    TensorBox,
                    ir.Constant,
                    type(None),
                    ir.ConstantBuffer,
                    sympy.Expr,
                    sympy.logic.boolalg.Boolean,
                    int,
                    ir.EffectfulKernel,
                    ir.ShapeAsConstantBuffer,
                    TorchBindObject,
                    ir.OpaqueMultiOutput,
                    ir.OpaqueValueTypeConstant,
                    ir.OpaqueObjectState,
                ),
            )
            for x in result
        ), result

        fx_node_args = V.graph.current_node.args[0]  # type: ignore[arg-type]
        if not isinstance(fx_node_args, (tuple, list)):
            # nested subgraphs can have singleton outputs
            fx_node_args = (fx_node_args,)
        result = [ir.ExternKernel.realize_input(x) for x in result]
        result_correct_strides = []

        assert len(fx_node_args) == len(result)
        for r, fx_node in zip(result, fx_node_args):
            if not isinstance(r, (ir.TensorBox, ir.BaseView)):
                result_correct_strides.append(r)
            elif isinstance(r.get_output_spec(), ir.CommBufferLayout):
                # Active references to persistent comm buffers are not allowed
                # outside of graphs
                result_correct_strides.append(ir.ExternKernel.copy_input(r))
            else:
                # AOT Autograd tries to detect stride divergence of inductor from output metadata.
                # Here, we try to avoid spurious divergence by matching insignificant strides such as

                # should have already been realized
                assert torch._inductor.ir.is_storage_and_layout(r)
                meta_strides = [
                    s.node.expr if isinstance(s, torch.SymInt) else s
                    # pyrefly: ignore [missing-attribute]
                    for s in fx_node.meta["val"].stride()
                ]
                result_correct_strides.append(
                    ir.try_match_insignificant_strides(r, meta_strides)
                )

        self.graph_outputs = result_correct_strides
        value: ir.IRNode
        for name, value in self.graph_inputs.items():
            if isinstance(
                value,
                (
                    TorchBindObject,
                    sympy.Basic,
                    torch._inductor.ir.GeneratorState,
                    torch._inductor.ir.OpaqueObjectState,
                ),
            ):
                continue
            assert isinstance(value, TensorBox), (
                f"Unsupported inductor graph input type: {type(value)}"
            )
            value.realize()
            assert isinstance(value, TensorBox)
            value = value.data
            assert isinstance(value, ir.StorageBox)
            value_storage_box = value
            value = value.data
            if not isinstance(value, InputBuffer) or value.get_name() != name:
                # one of our inputs was mutated, need to turn that into a copy
                ir.MutationLayoutSHOULDREMOVE.realize_into(
                    value, self.graph_inputs_original[name]
                )
                # replace output with mutated input
                try:
                    ind = self.graph_outputs.index(value_storage_box)
                    self.graph_outputs[ind] = self.graph_inputs_original[name]
                except ValueError:
                    pass

        self.finalize()
        log.debug(
            "Force channels last inputs for %d conv for the current graph with id %d",
            self.num_channels_last_conv,
            self.graph_id if self.graph_id is not None else -1,
        )