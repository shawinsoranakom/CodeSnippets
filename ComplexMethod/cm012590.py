def masked(mask, body, other):
        if mask is not None and torch.version.hip is not None:
            mask = V.kernel.cse.generate(
                V.kernel.compute,
                f"{mask}.to(tl.int1)",
                dtype=torch.bool,
                shape=mask.shape,
            )

        nodes = body.graph.find_nodes(op="output")
        assert nodes, "graph for body does not contain an output"

        need_where = False
        # If we have a tl.load with a masking operator and no other value
        # we can add the mask here and the other value to the tl.load
        # operator to save the branching cost.
        for node in nodes:
            for arg in node.args:
                if arg.target != "load" or should_unwrap_unspec_arg(arg.args[1]):
                    need_where = True
                    break

        value = None if need_where else other

        with V.kernel.mask_loads(mask, value=value) as new_mask:
            result = body()

        if need_where:
            # Remove once CSEVariables track the dtype
            if result.bounds.is_bool:
                other = bool(other)
            # Take dtype from result to prevent accidental promotion
            other = V.kernel.cse.generate(
                V.kernel.compute,
                f"tl.full({result}.shape, {constant_repr(other)}, {result}.dtype)",
                bounds=ValueRanges.wrap(other),
                dtype=result.dtype,
                shape=result.shape,
            )
            ret = ops.where(new_mask, result, other)
        else:
            ret = result

        ret.mask_vars.discard(new_mask)
        return ret