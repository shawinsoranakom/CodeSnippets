def _build(branch_idx):
        inner_outputs = None
        then_params, then_body, then_raw = _trace_branch(branches[branch_idx])
        if branch_idx == n - 2:
            else_params, else_body, _ = _trace_branch(branches[branch_idx + 1])
        else:
            inner_outputs, _ = _build(branch_idx + 1)
            else_params, pt_results = [], []
            for inner_out in inner_outputs:
                ep = ov_opset.parameter(
                    inner_out.get_partial_shape(),
                    inner_out.get_element_type(),
                )
                else_params.append(ep)
                pt_results.append(ep.output(0))
            else_body = Model(pt_results, else_params)

        cond = ov_opset.equal(
            index_ov,
            ov_opset.constant(branch_idx, Type.i32).output(0),
        ).output(0)
        if_node = ov_opset.if_op(cond)
        if_node.set_then_body(then_body)
        if_node.set_else_body(else_body)

        if inner_outputs is None:
            for ov_inp, tp, ep in zip(operands_ov, then_params, else_params):
                if_node.set_input(ov_inp, tp, ep)
        else:
            for ov_inp, tp in zip(operands_ov, then_params):
                if_node.set_input(ov_inp, tp, None)
            for inner_out, ep in zip(inner_outputs, else_params):
                if_node.set_input(inner_out, None, ep)

        outputs = [
            if_node.set_output(then_body.results[i], else_body.results[i])
            for i in range(len(then_body.results))
        ]
        return outputs, then_raw