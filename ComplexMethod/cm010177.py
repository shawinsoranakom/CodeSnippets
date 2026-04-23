def replace_quantized_ops_with_standard_ops(gm: torch.fx.GraphModule):
    """
    Replace legacy quantized ops (aten.quantize_per_tensor, quantized.conv) with
    PT2 ops (quantize_decomposed.quantize_per_tensor, aten.conv).

    Before:    x || -> aten.q        || -> quantized.conv2d     || -> quantized.linear    || -> aten.dq || -> y

    After:     x || -> qd.q -> qd.dq || -> aten.conv2d -> qd.q -> qd.dq || aten.linear -> qd.q -> qd.dq || -> y

    (qd == quantized_decomposed library, q = quantize, dq = dequantize)
                                          ^
                                          |
                getattr(w), getattr(b) from Conv2dParamPrepack

    During each iteration, the transformation spits out the transformed operator, its quantized output,
    and its dequantized value together. We did this because dequantization need to use the
    scale and zero point parameters from the quantization to recover the approximate original value. After each
    iteration, the new dequantization node will be used as the input to the next node (e.g., dq2 -> linear).

    For operators like conv2d and linear, their weights and bias are packed in a quantized format in the ScriptObject.
    During the transformation, we unpack those objects, get their dequantized tensor, populate those
    as attributes to the module, and use getattr to access them.

    One exception in the transformation is conv_prepack and linear_prepack. Those calls pack
    weight and bias constant tensors into ScriptObject, which are then used by subsequent conv2d or linear calls.
    During transformation, we directly skip transforming conv_prepack or linear_prepack. We check whether ScriptObject to the
    quantized::conv2d or linear is from conv_prepack or linear_prepack. If it is, we then inline those parameters
    to the operator by converting them to a getattr fx.node.

    For prepacked::conv2d_clamp_run and prepacked::linear_clamp_run, we directly convert them to aten.conv2d and aten.linear
    without the need of doing de/quantization.

    Three global variables defined are _INPUT_Q_DTYPE, _SCALE, _ZERO_POINT. _INPUT_Q_DTYPE determines the de/quantization
    data type, which is the same across the entire program, but it only shows up in the very first quantization
    call. _SCALE and _ZERO_POINT are used only when operators do not have those specified. E.g., mul.Scalar.
    """

    global _INPUT_Q_DTYPE

    quantized = False

    last_quantized_node = None
    # pyrefly: ignore [bad-assignment]
    for node in gm.graph.nodes:
        if isinstance(node.target, OpOverload):
            with gm.graph.inserting_before(node):
                namespace, opname = node.target.namespace, node.target._opname
                if namespace == "quantized" and opname not in [
                    "conv_prepack",
                    "linear_prepack",
                ]:
                    quantized = True
                    fx_node = fx_transform_quantized_op_to_standard_op(gm, node)
                    node.replace_all_uses_with(fx_node)
                    last_quantized_node = fx_node
                elif namespace == "prepacked":
                    quantized = True
                    fx_node = _transform_prepacked_op(gm, node)
                    node.replace_all_uses_with(fx_node)
                    last_quantized_node = fx_node
                elif namespace == "aten" and opname == "quantize_per_tensor":
                    inp_node, scale_node, zero_point_node, dtype_node = node.args
                    dtype_node = fx_enum_to_dtype(gm, dtype_node)
                    _INPUT_Q_DTYPE = dtype_node
                    qmin_node, qmax_node = insert_qmin_qmax_node(gm, dtype_node)
                    q_fx_node = insert_quantized_node(
                        gm,
                        inp_node,
                        scale_node,
                        zero_point_node,
                        qmin_node,
                        qmax_node,
                        dtype_node,
                        torch.per_tensor_affine,
                    )
                    dq_fx_node = insert_dequantized_node(
                        gm,
                        q_fx_node,
                        scale_node,
                        zero_point_node,
                        qmin_node,
                        qmax_node,
                        dtype_node,
                        None,
                        torch.per_tensor_affine,
                    )
                    node.replace_all_uses_with(dq_fx_node)
                    last_quantized_node = dq_fx_node
                elif namespace == "aten" and opname == "dequantize":
                    if last_quantized_node is None:
                        raise AssertionError("last_quantized_node should not be None")
                    node.replace_all_uses_with(last_quantized_node)
                else:
                    last_quantized_node = node

    # Post-processing again to remove legacy ScriptObjects and quantizated tensors
    # stored as attributes or in the buffer. This is used to clean up the GraphModule
    # to not trigger tracing errors like missing __obj_flatten__ functions.
    def _clean_attr(mod: torch.nn.Module):
        for submod in mod.modules():
            attr_names_to_clean = set()
            for k, v in submod.__dict__.items():
                if isinstance(v, torch.ScriptObject):
                    attr_names_to_clean.add(k)
                if k == "_buffers":
                    buffer_name_to_clean = set()

                    for b_name, b_value in v.items():
                        if isinstance(b_value, torch.Tensor) and b_value.dtype in [
                            torch.qint8,
                            torch.quint8,
                        ]:
                            buffer_name_to_clean.add(b_name)
                    for b_name in buffer_name_to_clean:
                        v.pop(b_name, None)
            for attr_name in attr_names_to_clean:
                delattr(submod, attr_name)

    if quantized:
        """
        TODO: SetAttr + quantized ops will result incorrect program. This flag is used to temporarily
        bypass test cases.

        The deadcode elimination pass is needed to remove legacy quantized ops. Otherwise, retracing
        will throw errors. However, the current way of SetAttr does inplace update to attributes, so
        this pass regard them as dead code and remove them. Below is an example of GraphModule before
        and after the dead code elimination pass.

        class GraphModule(torch.nn.Module):
            def forward(self, x_1):
                # No stacktrace found for following nodes
                data = self.data;  data = None
                data_1 = self.data
                add_tensor = torch.ops.aten.add.Tensor(data_1, x_1, alpha = 1);  data_1 = None
                data_2 = self.data
                copy_ = torch_Tensor_copy_(data_2, add_tensor);  data_2 = add_tensor = copy_ = None
                data_3 = self.data
                add_tensor_1 = torch.ops.aten.add.Tensor(x_1, data_3, alpha = 1);  x_1 = data_3 = None
                return add_tensor_1

        class GraphModule(torch.nn.Module):
            def forward(self, x_1):
                # No stacktrace found for following nodes
                data_3 = self.data
                add_tensor_1 = torch.ops.aten.add.Tensor(x_1, data_3, alpha = 1);  x_1 = data_3 = None
                return add_tensor_1
        """
        gm.graph.eliminate_dead_code()
        _clean_attr(gm)