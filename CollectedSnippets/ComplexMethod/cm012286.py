def _find_reshape_mm_reshape(node: torch.fx.Node) -> list[_Matmul]:
    if node.target != aten.reshape.default:
        return []

    matches = []
    for mm_node in node.users:
        if mm_node.target not in (aten.mm.default, aten._scaled_mm.default):
            continue
        for reshape_node in mm_node.users:
            if reshape_node.target != aten.reshape.default:
                continue

            # Since the reshape -> mm -> reshape pattern would be subsumed into
            # the fused op, we only match the patterns where the shape of the
            # second reshape is matches the mm result produced by the fused op.
            matmul_input_node = cast("torch.fx.Node", node.args[0])
            B_node = cast("torch.fx.Node", mm_node.args[1])
            matmul_out_shape = torch.Size(
                [
                    *_get_tensor(matmul_input_node).shape[:-1],
                    _get_tensor(B_node).shape[-1],
                ]
            )
            if _get_tensor(reshape_node).shape != matmul_out_shape:
                continue
            matches.append([node, mm_node, reshape_node])
            # If for some rare reason mm_node is being reshaped by two
            # different reshape nodes, we only include mm_node once in the
            # parsing result.
            break

    matmuls = []
    for match in matches:
        mm_node = match[1]
        if mm_node.target is aten.mm.default:
            matmul = _Matmul.from_match(match)
            matmuls.append(matmul)
        elif mm_node.target is aten._scaled_mm.default:
            matmul = _ScaledMatmul.from_match(match)
            matmuls.append(matmul)
        else:
            raise AssertionError(
                "Expect the node's target to be either aten.mm.default or "
                f"aten._scaled_mm.default. Got {mm_node.target}."
            )
    return matmuls