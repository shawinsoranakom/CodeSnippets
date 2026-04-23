def test_beam_search_passes_multimodal_data(
    monkeypatch,
    hf_runner,
    vllm_runner,
    dtype: str,
    max_tokens: int,
    beam_width: int,
) -> None:
    """Ensure that beam search passes multimodal data through correctly."""
    if current_platform.is_rocm():
        monkeypatch.setenv("VLLM_ROCM_USE_SKINNY_GEMM", "0")

    # NOTE - this test is primarily to check that mm data is passed to beams
    # correctly. As such, we just need to check one extra modality to make
    # sure things pass through properly.
    audios = [AudioAsset("mary_had_lamb").audio_and_sample_rate]
    model = "Qwen/Qwen2-Audio-7B-Instruct"
    audio_seq = "<|audio_bos|><|AUDIO|><|audio_eos|>"
    prompts = [
        f"<|im_start|>user\n{audio_seq}Can you transcribe this?<|im_end|>\n<|im_start|>assistant\n"  # noqa: E501
    ]

    with hf_runner(model, dtype=dtype, auto_cls=AutoModelForSeq2SeqLM) as hf_model:
        audio_token_id = hf_model.config.audio_token_index
        eos_token_id = hf_model.tokenizer.eos_token_id  # <|im_end|>
        hf_outputs = hf_model.generate_beam_search(
            prompts,
            beam_width=beam_width,
            max_tokens=max_tokens,
            audios=audios,
        )

    with vllm_runner(model, dtype=dtype, **EXTRA_ENGINE_KWARGS) as vllm_model:
        vllm_outputs = vllm_model.generate_beam_search(
            prompts,
            beam_width=beam_width,
            max_tokens=max_tokens,
            audios=audios,
        )

    seq_with_no_audio_toks = lambda seq: [tok for tok in seq if tok != audio_token_id]

    for i in range(len(prompts)):
        hf_output_ids, hf_output_texts = hf_outputs[i]
        vllm_output_ids, vllm_output_texts = vllm_outputs[i]

        for j, (hf_text, vllm_text) in enumerate(
            zip(hf_output_texts, vllm_output_texts)
        ):
            print(f">>>{j}-th hf output [NOTE: special tokens are filtered]:")
            print(hf_text)
            print(f">>>{j}-th vllm output:")
            print(vllm_text)
        assert len(hf_output_ids) == len(vllm_output_ids)

        for j in range(len(hf_output_ids)):
            # Compare everything except for the audio tokens; we do this since
            # the IDs returned from the transformers helper expands the audio
            # token to match features, while the vLLM helper maintains the
            # single audio token in the input text
            filtered_hf_output_ids = seq_with_no_audio_toks(hf_output_ids[j])
            filtered_vllm_output_ids = seq_with_no_audio_toks(vllm_output_ids[j])

            # HF output IDs may contain the end of sequence
            if len(filtered_hf_output_ids) == len(filtered_vllm_output_ids) + 1:
                assert filtered_hf_output_ids[-1] == eos_token_id
                filtered_hf_output_ids = filtered_hf_output_ids[:-1]

            assert filtered_hf_output_ids == filtered_vllm_output_ids