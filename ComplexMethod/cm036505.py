def _granite4_vision_vllm_to_hf_output(vllm_output, model):
    """Post-processor for granite4_vision vLLM output.

    Self-contained to avoid calling AutoConfig/AutoTokenizer without
    trust_remote_code (needed while the model is not in upstream HF).
    """
    output_ids, output_str, out_logprobs = vllm_output
    mm_token_id = 100352
    hf_output_ids = [
        token_id
        for idx, token_id in enumerate(output_ids)
        if token_id != mm_token_id or idx == 0 or output_ids[idx - 1] != mm_token_id
    ]
    hf_output_str = (
        output_str[1:] if output_str and output_str[0] == " " else output_str
    )
    eos_token_id = 100257
    if hf_output_ids and hf_output_ids[-1] == eos_token_id:
        hf_output_str = hf_output_str + "<|end_of_text|>"
    return hf_output_ids, hf_output_str, out_logprobs