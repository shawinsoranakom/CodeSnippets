def test_dynamo_rewrite_dist_allreduce(self, pg_mode):
        def func(tensor, *args, **kwargs):
            torch.distributed.all_reduce(
                tensor,
                *args,
                **kwargs,
            )

        counter = CompileCounter()
        compiled = torch.compile(func, backend=counter, fullgraph=True)

        args = []
        kwargs = {}

        if pg_mode == "positional":
            args.append(torch.distributed.ReduceOp.MAX)
            args.append(GroupMember.WORLD)
        elif pg_mode == "positional_none":
            args.append(torch.distributed.ReduceOp.MAX)
            args.append(None)
        elif pg_mode == "kwargs":
            kwargs["group"] = GroupMember.WORLD
        elif pg_mode == "kwargs_none":
            kwargs["group"] = None
        else:
            if pg_mode != "unspecified":
                raise AssertionError(f"Unexpected pg_mode: {pg_mode}")

        inputs_compiled = torch.ones(2, device=self.device)
        inputs_eager = torch.ones(2, device=self.device)

        compiled(inputs_compiled, *args, **kwargs)
        func(inputs_eager, *args, **kwargs)

        if counter.frame_count != 1:
            raise AssertionError(
                f"Expected frame_count == 1, got {counter.frame_count}"
            )
        # should test more precisely, but the 3 is supposed to be (all_reduce, wait, copy_)
        if counter.op_count != 3:
            raise AssertionError(f"Expected op_count == 3, got {counter.op_count}")
        if not same(inputs_compiled, inputs_eager):
            raise AssertionError("Expected inputs_compiled to match inputs_eager")