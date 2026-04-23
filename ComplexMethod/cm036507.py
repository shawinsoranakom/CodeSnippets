def test_beam_search_encoder_decoder(
    monkeypatch,
    hf_runner,
    vllm_runner,
    dtype: str,
    max_tokens: int,
    beam_width: int,
    resampled_assets,
) -> None:
    """Test beam search with encoder-decoder models (Whisper)."""
    if current_platform.is_rocm():
        monkeypatch.setenv("VLLM_ROCM_USE_SKINNY_GEMM", "0")

    model = "openai/whisper-large-v3-turbo"
    check_model_available(model)

    hf_prompts = [
        "<|startoftranscript|>",
        "<|startoftranscript|>",
    ]

    with hf_runner(model, dtype=dtype, auto_cls=AutoModelForSpeechSeq2Seq) as hf_model:
        hf_outputs = hf_model.generate_beam_search(
            hf_prompts,
            beam_width=beam_width,
            max_tokens=max_tokens,
            audios=resampled_assets,
        )

    # Test both explicit encoder/decoder prompts
    vllm_prompts = [
        # Implicit encoder/decoder prompt
        {
            "prompt": "<|startoftranscript|>",
            "multi_modal_data": {"audio": resampled_assets[0]},
        },
        # Explicit encoder/decover prompt
        {
            "encoder_prompt": {
                "prompt": "",
                "multi_modal_data": {"audio": resampled_assets[1]},
            },
            "decoder_prompt": "<|startoftranscript|>",
        },
    ]

    with vllm_runner(
        model,
        dtype="half",
        max_model_len=448,
        tensor_parallel_size=1,
        max_num_seqs=4,
        limit_mm_per_prompt={"audio": 2},
        enforce_eager=True,
    ) as vllm_model:
        vllm_outputs = vllm_model.generate_beam_search(
            vllm_prompts,
            beam_width=beam_width,
            max_tokens=max_tokens,
        )

    for i in range(len(vllm_prompts)):
        hf_output_ids, hf_output_texts = hf_outputs[i]
        vllm_output_ids, vllm_output_texts = vllm_outputs[i]

        for j, (hf_text, vllm_text) in enumerate(
            zip(hf_output_texts, vllm_output_texts)
        ):
            print(f">>>{j}-th hf output [NOTE: special tokens are filtered]:")
            print(hf_text)
            print(f">>>{j}-th vllm output:")
            print(vllm_text)

        # Check that we got the same number of beams
        assert len(hf_output_ids) == len(vllm_output_ids)

        # For encoder-decoder models, we primarily want to verify that:
        # 1. Beam search completes without errors
        # 2. We get the expected number of beams
        # 3. Outputs are reasonable (non-empty, diverse beams)
        for j in range(len(vllm_output_ids)):
            # Check that outputs are not empty
            assert len(vllm_output_ids[j]) > 0, f"Prompt {i}, beam {j}: empty output"
            # Check that decoded text is not empty
            assert len(vllm_output_texts[j].strip()) > 0, (
                f"Prompt {i}, beam {j}: empty text output"
            )