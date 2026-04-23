def batch_generate(
    model: AutoModelForCausalLM,
    simple_batch_inputs: list,
    generation_config: GenerationConfig,
    cb_config: ContinuousBatchingConfig,
    tokenizer: AutoTokenizer,
    displayed_samples: int = 0,  # -1: no display, 0: display stats, >0: display inputs and some outputs
    output_file: str | None = None,
    expected_outputs: list[str] | None = None,
) -> tuple[float, float]:
    # Actual batch generation
    batch_outputs = model.generate_batch(
        inputs=simple_batch_inputs,
        generation_config=generation_config,
        continuous_batching_config=cb_config,
    )
    generation_start = min(out.created_time for out in batch_outputs.values())
    generation_end = max(out.lifespan[1] for out in batch_outputs.values())

    if displayed_samples >= 0:
        print("Done with batch generation.")

    # Decode outputs
    token_count = 0
    data = []
    for i, request in enumerate(batch_outputs):
        input_text = tokenizer.decode(batch_outputs[request].prompt_ids, skip_special_tokens=False)
        # The key is used to tie back to the output of unbatched generation
        key = " ".join(map(str, batch_outputs[request].prompt_ids))
        data.append({"input": input_text, "key": key})

        # Try to decode the output
        try:
            output_text = tokenizer.decode(batch_outputs[request].generated_tokens, skip_special_tokens=False)
            token_count += len(batch_outputs[request].generated_tokens)
            data[-1]["cb_outputs"] = output_text
        except Exception as e:
            print(f"Decoding failed for request {request}: {e}")
            data[-1]["cb_outputs"] = "__ERROR__"
            continue

        # Display sample if asked
        if i < displayed_samples:
            print("-" * 20, f"{request} Input:  {input_text}", f"{request} Output: {output_text}", sep="\n")

        # Compare with classic generate if asked
        if expected_outputs is not None:
            expected_output = expected_outputs.pop(key)
            matches = output_text == expected_output  # TODO: rework this for a better distance metric
            data[-1]["without_cb"] = expected_output
            data[-1]["matches"] = matches
            data[-1].pop("key")
            print(f"Request {i} matches" if matches else f"Request {i} does NOT match!")

    # Compute stats and maybe print them
    gen_time = generation_end - generation_start
    tok_per_sec = token_count / gen_time
    if displayed_samples >= 0:
        print("-" * 20)
        print("--- Finished CB Generation Example ---\n")
        print(f"CB generation took: {gen_time:.2f} seconds for {token_count} tokens. {tok_per_sec:.2f}tok/s")
    stats = {
        "num_blocks": cb_config.num_blocks,
        "max_batch_tokens": cb_config.max_batch_tokens,
        "max_blocks_per_request": cb_config.max_blocks_per_request,
        "use_cuda_graph": cb_config.use_cuda_graph,
        "use_async_batching": cb_config.use_async_batching,
        "use_default_compile_configs": cb_config.use_default_compile_configs,
        "gen_time": gen_time,
        "token_count": token_count,
        "tok_per_sec": tok_per_sec,
    }

    # If an output file is provided, save the reordered data to it
    data.sort(key=lambda x: x["input"])
    data = [stats] + data
    if output_file is not None:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)

    return gen_time, tok_per_sec