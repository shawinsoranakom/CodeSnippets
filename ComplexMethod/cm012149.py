def check_int8_woq_concat_linear_weights(match):
        is_cpu = match.kwargs["inp"].meta["val"].is_cpu
        if not is_cpu or not config.cpp.enable_concat_linear:
            # Currently, this pattern is only supported on CPU
            return False

        weight_inputs = ["w1", "w2"]
        if "w3" in match.kwargs:
            weight_inputs.append("w3")

        if not all(
            match.kwargs[wgt].target is torch.ops.prims.convert_element_type.default
            for wgt in weight_inputs
        ):
            return False

        if not all(
            next(iter(match.kwargs[wgt]._input_nodes.keys())).meta["val"].dtype
            is torch.int8
            for wgt in weight_inputs
        ):
            return False

        if not all(
            match.kwargs[wgt].meta["val"].dtype is torch.bfloat16
            for wgt in weight_inputs
        ):
            return False

        return True