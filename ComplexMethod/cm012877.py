def _maybe_insert_output_observer_for_node(
    node: Node,
    model: torch.nn.Module,
    named_modules: dict[str, torch.nn.Module],
    graph: Graph,
    obs_or_fq_map: dict[EdgeOrNode, ObserverOrFakeQuantize],
    is_qat: bool,
) -> Node | None:
    """
    If `node` needs an output observer, creates it, inserts it into `graph`
    and returns it.

    If `node` does not need an output observer, returns None.

    Note: inserting dynamic quantization ops for output is not supported in fx graph mode
    quantization code path right now
    """
    if node.op == "output":
        raise AssertionError("observer insertion for outputs is handled elsewhere")

    is_standalone_module = False
    if "quantization_annotation" in node.meta:
        raise NotImplementedError(
            "Please use torchao (https://github.com/pytorch/ao) for pt2e quantization flow"
        )

    if "target_dtype_info" not in node.meta:
        raise AssertionError("expected 'target_dtype_info' in node.meta")
    is_standalone_module = node.meta["target_dtype_info"].get(
        "_is_standalone_module", False
    )
    output_act_obs_or_fq_ctr = node.meta["target_dtype_info"].get(
        "output_act_obs_or_fq_ctr"
    )
    output_act_obs_or_fq = (
        output_act_obs_or_fq_ctr() if output_act_obs_or_fq_ctr else None
    )
    target_dtype, target_is_dynamic = _get_dtype_and_is_dynamic(output_act_obs_or_fq)
    # uncomment after we support reuse_input_obs_or_fq properly by having separate
    # implementations for this key instead of reusing the input_output_share_observers
    # code
    # reuse_input_obs_or_fq = node.meta["target_dtype_info"].get("reuse_input_obs_or_fq", False)
    # for now we set this to False since reuse_input_obs_or_fq for
    # the output of a node is implementation in the same code path as observer sharing,
    # we should refactor this part to make it clearer in the future
    # and we would be able to read this from config directly
    reuse_input_obs_or_fq = False

    # Note: prev_output_dtype = torch.float and prev_output_is_dynamic=False
    # because the prev_output is the output of an fp32 op, although technically
    # we should get the dtype of the output from node.meta["val"] in the future
    # if we deprecate fx graph mode quantization
    needs_obs_or_fq = _needs_obs_or_fq(
        torch.float, False, target_dtype, target_is_dynamic, reuse_input_obs_or_fq
    )
    # currently the activation in QConfig(activation=...,) is for both input
    # and output, and when the activation is configured to be dynamic quantization
    # e.g. PlaceholderObserver(dtype=torch.quint8, is_dynamic=True, ...), it means
    # the input should by dynamically quantized, but output should not be quantized
    #
    # there is no way we can specify different observer/fq for input and output
    # activation through QConfig today, this limitation is lifted in the
    # quantizer/annotation API in pytorch 2.0 export quantization code path,
    # but since this code is reused, annotating output to be dynamically quantized
    # would not work either for that.
    # we can change QConfig to support input/output activation if we want
    # to remove the following check, or if we can deprecate fx graph mode quantization
    if target_is_dynamic:
        needs_obs_or_fq = False

    # we never insert observers to output of standalone module, we assume
    # if needed, they are inserted inside the standalone module
    needs_obs_or_fq = needs_obs_or_fq and (not is_standalone_module)

    if needs_obs_or_fq:
        obs_or_fq_map[node] = output_act_obs_or_fq
        return _insert_obs_or_fq(
            node, output_act_obs_or_fq, model, named_modules, graph
        )
    else:
        return None