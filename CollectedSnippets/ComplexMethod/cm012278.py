def fn(match, *args, **kwargs):
            negative_slope = kwargs.get("negative_slope")
            if isinstance(negative_slope, ir.TensorBox):
                matched = False
            else:  # inp is a Number
                matched = True
            if lowp_dtype:
                dtype1 = kwargs.get("to_float")
                dtype2 = (
                    kwargs.get("to_bf16")
                    if lowp_dtype == torch.bfloat16
                    else kwargs.get("to_fp16")
                )
                matched = matched and dtype1 == torch.float and dtype2 == lowp_dtype
            computation_args = list(args)
            counters["inductor"]["mkldnn_unary_fusion_matcher_count"] += 1
            counters["inductor"]["mkldnn_unary_fusion_matcher_nodes"] += len(
                match.nodes
            )
            if matched:
                computation_args = computation_args[:-3] + [
                    "leaky_relu",
                    [negative_slope],
                    "",
                ]
                return L[computation_op](*computation_args)
            else:
                # computation_args += ["none", [], ""]
                out = L[computation_op](*computation_args)
                if lowp_dtype:
                    out = L[prims.convert_element_type.default](out, dtype=torch.float)
                out = L[aten.where](
                    L[aten.gt](out, 0),
                    out,
                    L[aten.mul](out, negative_slope),
                )
                if lowp_dtype:
                    out = L[prims.convert_element_type.default](out, dtype=dtype2)  # type: ignore[possibly-undefined]
                return out