def _check_conv_and_broadcast_op(conv_node, other):
        # According to checkConvAndBroadcastingOpPreConditions of frozen_conv_folding.cpp.
        # conv.weight
        if conv_node.args[1].op != "get_attr":
            return False
        # conv.bias
        if conv_node.args[1] is not None and conv_node.args[1].op != "get_attr":
            return False
        if (
            not isinstance(other, int)
            and not isinstance(other, float)
            and other.op != "get_attr"
        ):
            return False

        if len(conv_node.args[1].users) != 1:
            return False

        weight_meta_value = conv_node.args[1].meta.get("val")
        if weight_meta_value is None:
            return False
        # Avoid fusing op that causes type promotion
        # restricting to float avoids int/float difficulties with scalar overload
        if not weight_meta_value.is_floating_point():
            return False
        if isinstance(other, torch.fx.Node) and other.op == "get_attr":
            other_meta_value = other.meta.get("val")
            if not other_meta_value.is_floating_point():  # type: ignore[union-attr]
                return False
            if (
                torch.promote_types(other_meta_value.dtype, weight_meta_value.dtype)  # type: ignore[union-attr]
                != weight_meta_value.dtype
            ):
                if not conv_node.meta.get("_allow_mixed_dtype_folding", False):
                    return False

                if (
                    other_meta_value.dtype != torch.float  # type: ignore[union-attr]
                    and weight_meta_value.dtype not in (torch.float16, torch.bfloat16)
                ):
                    return False

            if not _op_not_broadcasting_with_conv(weight_meta_value, other_meta_value):
                return False
        elif not isinstance(other, float):
            return False

        return True