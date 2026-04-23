def _find_matches(
    prompt: _S,
    mm_prompt_updates: "MultiModalPromptUpdates",
    tokenizer: TokenizerLike | None,
    *,
    prev_end_idx: int = 0,
    current_result: "MultiModalPromptUpdatesApplyResult",
) -> tuple[UpdateMode | None, list[_MatchToApply]]:
    mode: UpdateMode | None = None
    mm_matches = dict[tuple[str, int], tuple[PromptTargetMatch, int]]()

    for modality, modality_updates in mm_prompt_updates.items():
        for item_idx, item_updates in enumerate(modality_updates):
            if current_result[modality][item_idx] is not None:
                continue  # Updates have already been applied for this item

            for update_idx, update in enumerate(item_updates):
                if (modality, item_idx) in mm_matches:
                    break  # Already found a match for this item

                for match in update.iter_matches(
                    prompt,
                    tokenizer,
                    start_idx=prev_end_idx,
                ):
                    # All matches should share the same mode
                    if mode is None:
                        mode = update.mode
                    elif mode != update.mode:
                        continue

                    mm_matches[(modality, item_idx)] = match, update_idx
                    break  # Get only the first valid match per item

    # Prioritize earlier matches
    matches_to_apply = sorted(mm_matches.items(), key=lambda item: item[1][0])

    # To avoid conflicts, only replace one non-empty item at a time
    if mode == UpdateMode.REPLACE:
        matches_to_apply_ = list[_MatchToApply]()
        has_non_empty_matches = False

        for item in matches_to_apply:
            _, (match, _) = item
            if match.start_idx == match.end_idx:
                matches_to_apply_.append(item)
            elif not has_non_empty_matches:
                has_non_empty_matches = True
                matches_to_apply_.append(item)

        matches_to_apply = matches_to_apply_

    return mode, matches_to_apply