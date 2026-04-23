def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        # call_function must check any unsupported arguments and graph-break.
        # It's safe to assume args/kwargs from orig_fn map 1:1 to args/kwargs of remapped_fn,
        # since that's the contract for putting a mapping in `traceable_collective_remaps`
        import torch.distributed as dist
        from torch.distributed._functional_collectives import REDUCE_OP_TO_STR

        # Merge args into kwargs so positional and keyword args
        # can be processed the same way.
        signature = inspect.signature(self.fn)
        kwargs = dict(signature.bind(*args, **kwargs).arguments)
        args = ()

        if "async_op" in kwargs and kwargs["async_op"].as_python_constant():
            unimplemented(
                gb_type="async_op=True for distributed collectives",
                context=f"{self.fn}, {args=}, {kwargs=}",
                explanation=f"`torch.compile` doesn't support `async_op=True for {self.fn}",
                hints=[
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        if self.fn == dist.batch_isend_irecv:
            if not config.enable_p2p_compilation:
                unimplemented(
                    gb_type="P2P compilation disabled for batch_isend_irecv",
                    context=f"{self.fn}",
                    explanation="P2P compilation is disabled.",
                    hints=[
                        "Set TORCHDYNAMO_ENABLE_P2P_COMPILATION=1 to enable.",
                    ],
                )

            p2p_ops = kwargs["p2p_op_list"]
            if not isinstance(p2p_ops, variables.ListVariable):
                raise torch._dynamo.exc.InternalTorchDynamoError(
                    "`P2POp` used incorrectly"
                )

            ops: list[VariableTracker] = list()
            peers = list()
            tags = list()
            tensors = list()
            group_var: VariableTracker | None = None

            for item in p2p_ops.items:
                if item.python_type() is not dist.P2POp:
                    raise torch._dynamo.exc.InternalTorchDynamoError(
                        "`P2POp` used incorrectly"
                    )

                op_var = item.var_getattr(tx, "op")
                if op_var.is_python_constant():
                    op = op_var.as_python_constant()
                    if op not in (dist.isend, dist.irecv):
                        raise torch._dynamo.exc.InternalTorchDynamoError(
                            f"unexpected P2POp op {op}"
                        )
                    op_var = variables.ConstantVariable.create(op.__name__)
                elif hasattr(op_var, "get_name"):
                    op_var = variables.ConstantVariable.create(op_var.get_name())
                else:
                    raise torch._dynamo.exc.InternalTorchDynamoError(
                        f"unexpected P2POp op variable {op_var}"
                    )

                ops.append(op_var)
                tensors.append(item.var_getattr(tx, "tensor"))
                peers.append(item.var_getattr(tx, "peer"))
                tags.append(item.var_getattr(tx, "tag"))
                if group_var is None:
                    group_var = item.var_getattr(tx, "group")

            assert group_var is not None
            new_args: tuple[VariableTracker, ...] = ()
            new_kwargs: dict[str, VariableTracker] = {
                "op_list": variables.ListVariable(ops),
                "peer_list": variables.ListVariable(peers),
                "tag_list": variables.ListVariable(tags),
                "tensors": variables.ListVariable(tensors),
                "group_name": group_var,
            }
            return self.replacement_var.call_function(tx, new_args, new_kwargs)

        if self.fn in (dist.isend, dist.irecv):
            if not config.enable_p2p_compilation:
                unimplemented(
                    gb_type="P2P compilation disabled for isend/irecv",
                    context=f"{self.fn}",
                    explanation="P2P compilation is disabled.",
                    hints=[
                        "Set TORCHDYNAMO_ENABLE_P2P_COMPILATION=1 to enable.",
                    ],
                )

            return self.replacement_var.call_function(tx, args, kwargs)

        if self.fn in (
            dist.all_reduce,
            dist.reduce_scatter_tensor,
            # pyrefly: ignore [deprecated]
            dist._reduce_scatter_base,
        ):
            reduce_op_var = kwargs.get("op")
            reduce_op = (
                reduce_op_var.value  # type: ignore[attr-defined]
                if reduce_op_var is not None
                else signature.parameters["op"].default
            )
            if reduce_op not in REDUCE_OP_TO_STR:
                raise ValueError(f"Unsupported all_reduce op: {reduce_op}")
            kwargs["op"] = VariableTracker.build(tx, REDUCE_OP_TO_STR[reduce_op])
        return self.replacement_var.call_function(tx, args, kwargs)