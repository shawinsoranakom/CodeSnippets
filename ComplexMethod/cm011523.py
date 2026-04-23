def _compare_outputs(
    local_output: Any,
    ground_truth: torch.Tensor | list[torch.Tensor],
    output_placements: tuple[Placement, ...],
    mesh: DeviceMesh,
    world_size: int,
) -> tuple[bool, str]:
    """Compare op output (wrapped as DTensor) against ground truth."""
    if isinstance(local_output, (list, tuple)):
        local_outputs = list(local_output)
    else:
        local_outputs = [local_output]

    if isinstance(ground_truth, list):
        ground_truths = ground_truth
    else:
        ground_truths = [ground_truth]

    if len(local_outputs) != len(ground_truths):
        return (
            False,
            f"Output count mismatch: got {len(local_outputs)}, "
            f"expected {len(ground_truths)}",
        )

    if len(local_outputs) != len(output_placements):
        return (
            False,
            f"Output count mismatch with placements: "
            f"got {len(local_outputs)}, expected {len(output_placements)}",
        )

    for i, (local_out, gt, out_plc) in enumerate(
        zip(local_outputs, ground_truths, output_placements)
    ):
        if not isinstance(local_out, torch.Tensor):
            return False, f"Local output[{i}] is not a tensor: {type(local_out)}"

        if not isinstance(local_out, LocalTensor):
            return False, f"LocalTensor inputs produced non-LocalTensor output[{i}]"

        output_dt = DTensor.from_local(
            local_out,
            mesh,
            (out_plc,),
            shape=gt.shape,
            stride=gt.stride(),
        )

        if isinstance(out_plc, Replicate):
            local_values = [local_out._local_tensors[r] for r in range(world_size)]
            all_same = all(
                torch.allclose(local_values[0], lv, atol=1e-5, rtol=1e-5)
                for lv in local_values[1:]
            )
            if not all_same:
                return (
                    False,
                    f"Replicate output[{i}] but local values differ across ranks",
                )

        full_output = output_dt.redistribute(mesh, (Replicate(),)).to_local()

        if isinstance(full_output, LocalTensor):
            full_output = full_output._local_tensors[0]

        if gt.shape != full_output.shape:
            return (
                False,
                f"Shape mismatch[{i}]: expected {gt.shape}, got {full_output.shape}",
            )

        if not torch.allclose(gt, full_output, atol=1e-5, rtol=1e-5, equal_nan=True):
            max_diff = (gt - full_output).abs().max().item()
            return False, f"Value mismatch[{i}]: max_diff={max_diff:.6f}"

    return True, ""