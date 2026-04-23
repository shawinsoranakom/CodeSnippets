def evaluate_output(input, output, golden_output):
    # todo: how to make sure this handles denormals in the input well?
    # for now, only handle it if the inputs have the same shape, otherwise assume there are none
    # handle more than one input

    input = [i.flatten().float() for i in input if i.shape == output.shape]

    dtype = golden_output.dtype

    output = output.flatten().float()
    golden_output = golden_output.flatten().float()

    # we are checking subnormals separate from the rest of the numbers
    # we also need to check NaNs and Infs carefully

    subnormal_mask = golden_output.abs() < torch.finfo(dtype).smallest_normal
    for i in input:
        subnormal_mask |= i.abs() < torch.finfo(dtype).smallest_normal
    nan_mask_golden = torch.isnan(golden_output)
    golden_output = torch.where(nan_mask_golden, float("nan"), golden_output)
    nan_mask_output = torch.isnan(output)
    output = torch.where(nan_mask_output, float("nan"), output)

    equal_mask = (output == golden_output) | (nan_mask_golden & nan_mask_output)
    equal_subnormal_mask = (
        torch.where(subnormal_mask, 0, output)
        == torch.where(subnormal_mask, 0, golden_output)
    ) | equal_mask
    output_flushed = torch.where(subnormal_mask, 0.0, output)
    golden_flushed = torch.where(subnormal_mask, 0.0, golden_output)
    output_flushed = torch.where(~torch.isfinite(output_flushed), 0.0, output_flushed)
    golden_flushed = torch.where(~torch.isfinite(golden_flushed), 0.0, golden_flushed)

    num_nonequal = (~equal_mask).sum().item()
    num_nonequal_subnormal = (~equal_subnormal_mask).sum().item()

    err = rel_err_ulp(output_flushed, golden_flushed, dtype)
    max_ulp_to_golden = err.max().item()
    avg_ulp_to_golden = err.mean().item()
    mismatch_sample = []
    pos = (~equal_mask).nonzero().squeeze(1)
    log.info(
        "pos.shape: %s, input: %s, golden_output.shape: %s, output.shape: %s",
        pos.shape,
        [i.shape for i in input],
        golden_output.shape,
        output.shape,
    )
    ordered = torch.argsort(err[pos], descending=True)
    random = torch.randperm(pos.shape[0])
    for sampling in [ordered, random]:
        for i in range(min(pos.shape[0], 5)):
            sample_idx = pos[sampling[i]]
            mismatch_sample.append(
                {
                    "pos": sample_idx.item(),
                    "input": [inp[sample_idx].item() for inp in input],
                    "output": output[sample_idx].item(),
                    "golden": golden_output[sample_idx].item(),
                    "rel_err": err[sample_idx].item(),
                }
            )

    # use hashlib.sha256 to hash the tensors
    # this i
    return {
        "normal_hash": hashlib.sha256(
            output_flushed.cpu().numpy().tobytes()
        ).hexdigest()[:8],
        "full_hash": hashlib.sha256(output.cpu().numpy().tobytes()).hexdigest()[:8],
        "max_ulp_to_golden": max_ulp_to_golden,
        "avg_ulp_to_golden": avg_ulp_to_golden,
        "num_nonequal": num_nonequal,
        "num_nonequal_subnormal": num_nonequal_subnormal,
        "num_total": output.shape[0],
        "match_full": num_nonequal == 0,
        "match_normal": num_nonequal_subnormal == 0,
        "mismatch_sample": mismatch_sample,
    }