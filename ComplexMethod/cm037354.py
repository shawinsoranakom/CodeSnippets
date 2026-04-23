def _execute_local(
        self,
        mm_kwargs: dict[str, Any],
    ) -> list[torch.Tensor]:
        """Execute encoder on local inputs using greedy-packed CUDA graphs.

        Sort images by output token count (smallest first), then greedily pack
        as many images as possible into each batch while staying within
        max_budget tokens and max_batch_size. Once a batch is finalised (next
        image would overflow either constraint), find the smallest fitting
        budget once for that batch.

        By exchange argument, greedy smallest-first packing minimises eager
        fallbacks -- any other ordering yields a higher token sum in some batch,
        making that batch more likely to exceed the budget.

        Stats note:
          graph_hits  -- counted inside _run_budget_graph after successful replay.
          graph_misses -- counted here for single-image batches where the image
                         exceeds max_budget. Batches split due to max_batch_size
                         always satisfy total_tokens <= max_budget and therefore
                         always find a valid budget (no miss).
        """
        num_items = self.model.get_encoder_cudagraph_num_items(mm_kwargs)
        max_budget = self.token_budgets[-1]

        per_item_out_tokens = self._get_per_item_out_tokens(mm_kwargs)

        # Sort ascending by output token count (smallest first)
        sorted_indices = sorted(range(num_items), key=lambda i: per_item_out_tokens[i])

        # Greedy pack against max_budget and max_batch_size.
        # _find_smallest_fitting_budget_given_tokens is called once per
        # finalised batch, not per image.
        batches: list[tuple[list[int], int | None]] = []
        current_batch: list[int] = []
        current_batch_tokens = 0

        for orig_idx in sorted_indices:
            item_tokens = per_item_out_tokens[orig_idx]
            if (
                current_batch_tokens + item_tokens <= max_budget
                and len(current_batch) < self.max_batch_size
            ):
                current_batch.append(orig_idx)
                current_batch_tokens += item_tokens
            else:
                if current_batch:
                    batches.append(
                        (
                            current_batch,
                            self._find_smallest_fitting_budget_given_tokens(
                                current_batch_tokens
                            ),
                        )
                    )
                current_batch = [orig_idx]
                current_batch_tokens = item_tokens

        if current_batch:
            batches.append(
                (
                    current_batch,
                    self._find_smallest_fitting_budget_given_tokens(
                        current_batch_tokens
                    ),
                )
            )

        # outputs_by_orig_idx maps each original image index to its output
        # tensor. Needed because greedy packing reorders images; we restore
        # the original order before returning.
        outputs_by_orig_idx: dict[int, torch.Tensor] = {}

        for batch_orig_indices, token_budget in batches:
            batch_mm_kwargs = self.model.select_encoder_cudagraph_items(
                mm_kwargs, batch_orig_indices
            )
            batch_out_tokens = sum(per_item_out_tokens[i] for i in batch_orig_indices)

            if token_budget is None:
                # Single oversized image: item_tokens > max_budget.
                # graph_misses counted here for this eager fallback.
                logger.debug(
                    "Encoder CUDA graph fallback to eager: no budget for "
                    "%d tokens from %d images",
                    batch_out_tokens,
                    len(batch_orig_indices),
                )
                self.graph_misses += len(batch_orig_indices)
                with torch.inference_mode():
                    raw = self.model.encoder_eager_forward(batch_mm_kwargs)
                self._scatter_output_slices(
                    raw,
                    batch_orig_indices,
                    per_item_out_tokens,
                    outputs_by_orig_idx,
                )
            else:
                logger.debug(
                    "Encoder CUDA graph: batch_size=%d, tokens=%d, "
                    "budget=%d, waste=%.1f%%",
                    len(batch_orig_indices),
                    batch_out_tokens,
                    token_budget,
                    (token_budget - batch_out_tokens) / token_budget * 100,
                )
                replay = self.model.prepare_encoder_cudagraph_replay_buffers(
                    batch_mm_kwargs,
                    self.max_batch_size,
                    self.max_frames_per_batch,
                )

                # graph_hits counted inside _run_budget_graph after replay.
                output = self._run_budget_graph(
                    batch_mm_kwargs, token_budget, replay.buffers
                )
                assert output is not None
                self._scatter_output_slices(
                    output,
                    batch_orig_indices,
                    per_item_out_tokens,
                    outputs_by_orig_idx,
                    clone=True,
                )

        # Return in original batch order (caller maps outputs to token positions)
        return [outputs_by_orig_idx[i] for i in range(num_items)]