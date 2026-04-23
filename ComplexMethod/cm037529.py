def _iter_placeholders(
    prompt: list[int],
    mm_prompt_updates: "MultiModalPromptUpdates",
    tokenizer: TokenizerLike | None,
) -> Iterable[PlaceholderFeaturesInfo]:
    """
    Yield each set of placeholder tokens found in `prompt`.

    Matches are exclusive even when multiple modalities share
    the same placeholder tokens. In that case, the modality that
    appears earlier in `mm_prompt_updates` takes priority.

    Note that empty matches are ignored.
    """
    mm_item_counts = {m: len(items) for m, items in mm_prompt_updates.items()}
    item_idx_by_modality = {modality: 0 for modality in mm_prompt_updates}

    if _all_items_found(mm_item_counts, item_idx_by_modality):
        return

    prompt_len = len(prompt)
    start_idx = 0

    while start_idx < prompt_len:
        found = False

        for modality, modality_updates in mm_prompt_updates.items():
            item_idx = item_idx_by_modality[modality]
            if item_idx >= mm_item_counts.get(modality, 0):
                continue

            for update in modality_updates[item_idx]:
                content = update.content
                content_tokens_full = _seq2tokens(tokenizer, content.full)
                content_len_full = len(content_tokens_full)
                end_idx_full = start_idx + content_len_full

                if content_len_full == 0 or end_idx_full > prompt_len:
                    continue

                if prompt[start_idx:end_idx_full] == content_tokens_full:
                    content_is_embed = content.is_embed
                    if content_is_embed is not None:
                        content_is_embed = content_is_embed(tokenizer, content.full)

                    yield PlaceholderFeaturesInfo(
                        modality=modality,
                        item_idx=item_idx,
                        start_idx=start_idx,
                        tokens=content_tokens_full,
                        is_embed=content_is_embed,
                    )

                    # Exclude overlapping matches
                    start_idx = end_idx_full
                    item_idx_by_modality[modality] += 1
                    found = True
                    break

            if found:
                if _all_items_found(mm_item_counts, item_idx_by_modality):
                    return

                break  # Go back to the outer while loop

        if not found:
            start_idx += 1