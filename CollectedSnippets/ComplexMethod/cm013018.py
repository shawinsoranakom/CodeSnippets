def binary_cross_entropy_with_logits(
    g: jit_utils.GraphContext, input, target, weight, pos_weight, reduction
):
    p = g.op("Constant", value_t=torch.tensor([1]))
    sig_x = opset9.sigmoid(g, input)
    log_sig_x = opset9.log(g, sig_x)
    sub_1_x = opset9.sub(g, p, sig_x)
    sub_1_y = opset9.sub(g, p, target)
    log_1_x = opset9.log(g, sub_1_x)
    if pos_weight is None or symbolic_helper._is_none(pos_weight):
        output = opset9.neg(
            g,
            opset9.add(
                g, opset9.mul(g, target, log_sig_x), opset9.mul(g, sub_1_y, log_1_x)
            ),
        )
    else:
        output = opset9.neg(
            g,
            opset9.add(
                g,
                opset9.mul(g, opset9.mul(g, target, log_sig_x), pos_weight),
                opset9.mul(g, sub_1_y, log_1_x),
            ),
        )

    if weight is not None and not symbolic_helper._is_none(weight):
        output = opset9.mul(g, weight, output)

    reduction = symbolic_helper._maybe_get_const(reduction, "i")
    if reduction == 0:
        return output
    elif reduction == 1:
        return g.op("ReduceMean", output, keepdims_i=0)
    elif reduction == 2:
        return g.op("ReduceSum", output, keepdims_i=0)
    else:
        return symbolic_helper._onnx_unsupported(
            "binary_cross_entropy_with_logits with reduction other than none, mean, or sum",
            input,
        )