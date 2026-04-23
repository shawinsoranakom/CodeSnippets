def _check_linear_and_broadcast_op(linear_node, other, has_reshape):
        weight_node = (
            linear_node.args[2]
            if linear_node.target is aten.addmm.default
            else linear_node.args[1]
        )
        bias_node = (
            linear_node.args[0] if linear_node.target is aten.addmm.default else None
        )
        if weight_node.op != "get_attr":
            return False
        if bias_node is not None and bias_node.op != "get_attr":
            return False
        if (
            not isinstance(other, int)
            and not isinstance(other, float)
            and other.op != "get_attr"
        ):
            return False

        if len(weight_node.users) != 1:
            return False

        weight_meta_value = weight_node.meta.get("val")
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
                if not linear_node.meta.get("_allow_mixed_dtype_folding", False):
                    return False

                if (
                    other_meta_value.dtype != torch.float  # type: ignore[union-attr]
                    and weight_meta_value.dtype not in (torch.float16, torch.bfloat16)
                ):
                    return False

            if not _op_not_broadcasting_with_linear(
                weight_meta_value, other_meta_value, has_reshape
            ):
                return False
        elif not isinstance(other, float):
            return False

        return True