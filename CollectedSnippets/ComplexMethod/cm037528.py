def _apply_matches(
    prompt: _S,
    mm_prompt_updates: "MultiModalPromptUpdates",
    tokenizer: TokenizerLike | None,
) -> tuple[list[_S], "MultiModalPromptUpdatesApplyResult"]:
    mm_item_counts = {m: len(items) for m, items in mm_prompt_updates.items()}

    out_seqs = list[str | list[int]]()
    out_result: MultiModalPromptUpdatesApplyResult = {
        m: [None] * len(items) for m, items in mm_prompt_updates.items()
    }

    # Early exit if no items to find
    mm_found_counts = {
        m: sum(r is not None for r in res) for m, res in out_result.items()
    }
    if _all_items_found(mm_item_counts, mm_found_counts):
        return [prompt], out_result

    prev_end_idx = 0
    while True:
        mode, matches_to_apply = _find_matches(
            prompt,
            mm_prompt_updates,
            tokenizer,
            prev_end_idx=prev_end_idx,
            current_result=out_result,
        )

        if mode is None:
            break  # No more matches to find

        for (modality, item_idx), (match, update_idx) in matches_to_apply:
            matched_update = mm_prompt_updates[modality][item_idx][update_idx]
            matched_content = matched_update.content.full

            if mode == UpdateMode.INSERT:
                end_idx_to_insert = match.end_idx
            elif mode == UpdateMode.REPLACE:
                end_idx_to_insert = match.start_idx
            else:
                assert_never(mode)

            out_seqs.append(prompt[prev_end_idx:end_idx_to_insert])
            out_seqs.append(
                _seq2text(tokenizer, matched_content)
                if isinstance(prompt, str)
                else _seq2tokens(tokenizer, matched_content)
            )
            out_result[modality][item_idx] = update_idx

            # Exclude overlapping matches
            prev_end_idx = match.end_idx

        # Early exit if all items found
        mm_found_counts = {
            m: sum(r is not None for r in res) for m, res in out_result.items()
        }
        if _all_items_found(mm_item_counts, mm_found_counts):
            break

    out_seqs.append(prompt[prev_end_idx:])

    return cast(list[_S], out_seqs), out_result