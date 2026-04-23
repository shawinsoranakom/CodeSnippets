def _post_process_chunked(self, ctx: PoolingServeContext) -> None:
        # Online aggregation for chunked requests to
        # minimize memory usage
        # Track aggregation state for each prompt
        prompt_aggregators: dict[int, dict[str, Any]] = {}
        short_prompts_results: dict[int, PoolingRequestOutput] = {}
        for result_idx, result in enumerate(ctx.final_res_batch):
            if "-chunk-" not in result.request_id:
                # Non-chunked result - extract prompt_idx from request_id
                parts = result.request_id.split("-")
                try:
                    # Last part should be prompt index
                    prompt_idx = int(parts[-1])
                except (ValueError, IndexError):
                    prompt_idx = result_idx  # Fallback to result_idx

                short_prompts_results[prompt_idx] = result
            else:
                # Extract prompt_idx from chunked request_id
                parts = result.request_id.split("-")
                try:
                    prompt_idx = int(parts[parts.index("prompt") + 1])
                except (ValueError, IndexError):
                    # Fallback: extract from result_idx if parsing fails
                    prompt_idx = result_idx

                # Initialize aggregator for this prompt if needed
                if prompt_idx not in prompt_aggregators:
                    prompt_aggregators[prompt_idx] = {
                        "weighted_sum": None,
                        "total_weight": 0,
                        "chunk_count": 0,
                        "request_id": result.request_id.split("-chunk-")[0],
                    }

                aggregator = prompt_aggregators[prompt_idx]

                # MEAN pooling with online weighted averaging
                # Ensure result is PoolingRequestOutput
                # for embedding processing
                if not isinstance(result, PoolingRequestOutput):
                    raise ValueError(
                        f"Expected PoolingRequestOutput for "
                        f"chunked embedding, got "
                        f"{type(result).__name__}"
                    )
                if result.prompt_token_ids is None:
                    raise ValueError(
                        "prompt_token_ids cannot be None for chunked processing"
                    )

                weight = len(result.prompt_token_ids)
                embedding_data = result.outputs.data
                weighted_embedding = embedding_data.to(dtype=torch.float32) * weight

                if aggregator["weighted_sum"] is None:
                    # First chunk
                    aggregator["weighted_sum"] = weighted_embedding
                else:
                    # Accumulate
                    aggregator["weighted_sum"] += weighted_embedding

                aggregator["total_weight"] += weight
                aggregator["chunk_count"] += 1

        if ctx.original_engine_inputs is None:
            raise ValueError("Original engine inputs not available")

        original_engine_inputs = ctx.original_engine_inputs
        num_prompts = len(original_engine_inputs)

        # Finalize aggregated results
        final_res_batch: list[PoolingRequestOutput] = []
        for prompt_idx in range(num_prompts):
            if prompt_idx in prompt_aggregators:
                # Finalize MEAN aggregation for this chunked prompt
                aggregator = prompt_aggregators[prompt_idx]

                weighted_sum = aggregator["weighted_sum"]
                total_weight = aggregator["total_weight"]

                if (
                    weighted_sum is not None
                    and isinstance(weighted_sum, torch.Tensor)
                    and isinstance(total_weight, (int, float))
                    and total_weight > 0
                ):
                    # Compute final mean embedding
                    final_embedding = weighted_sum / total_weight

                    # Create a PoolingRequestOutput
                    # for the aggregated result
                    pooling_output_data = PoolingOutput(data=final_embedding)

                    # Get original prompt token IDs for this prompt
                    original_prompt = original_engine_inputs[prompt_idx]
                    token_ids = original_prompt.get("prompt_token_ids", None)
                    if token_ids is None:
                        raise NotImplementedError(
                            "Long Text Embedding with Chunked Processing does "
                            "not support EmbedsPrompt and EncoderDecoderInput."
                        )

                    original_token_ids = cast(list[int], token_ids)
                    pooling_request_output = PoolingRequestOutput(
                        request_id=aggregator["request_id"],
                        prompt_token_ids=original_token_ids,
                        outputs=pooling_output_data,
                        num_cached_tokens=0,
                        finished=True,
                    )

                    final_res_batch.append(pooling_request_output)
                else:
                    raise ValueError(
                        f"Failed to aggregate chunks for prompt {prompt_idx}"
                    )
            elif prompt_idx in short_prompts_results:
                final_res_batch.append(short_prompts_results[prompt_idx])
            else:
                raise ValueError(f"Result not found for prompt {prompt_idx}")

        ctx.final_res_batch = final_res_batch

        return None