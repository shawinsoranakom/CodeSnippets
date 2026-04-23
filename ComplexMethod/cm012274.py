def _is_packable_mkldnn_rnn_layer(match):
        lstm_node = match.output_node()
        POS_WEIGHTS = [1, 2]
        POS_INPUTS = [0, 5, 6]
        POS_ARGS = POS_WEIGHTS + POS_INPUTS
        # Weights should be Constant
        if any(
            lstm_node.args[POS_WEIGHT].op != "get_attr" for POS_WEIGHT in POS_WEIGHTS
        ):
            return False

        # Meta info for weights and inputs should be available
        if any(lstm_node.args[POS_ARG].meta.get("val") is None for POS_ARG in POS_ARGS):
            return False

        # Check device
        if any(
            lstm_node.args[POS_ARG].meta.get("val").device.type != "cpu"
            for POS_ARG in POS_ARGS
        ):
            return False

        # Check dtype
        if any(
            lstm_node.args[POS_ARG].meta.get("val").dtype == torch.bfloat16
            and not is_mkldnn_bf16_supported("cpu")
            for POS_ARG in POS_ARGS
        ):
            return False
        if any(
            lstm_node.args[POS_ARG].meta.get("val").dtype == torch.float16
            and not is_mkldnn_fp16_supported("cpu")
            for POS_ARG in POS_ARGS
        ):
            return False

        return True