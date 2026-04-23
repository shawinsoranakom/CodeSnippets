def prune_choices_postscreen(
        choices: list[ChoiceCaller],
        candidate_timings: dict[ChoiceCaller, float],
        name: str,
        inputs_key: str,
        prescreen_cache: dict[str, OrderedSet[str]],
    ) -> list[ChoiceCaller]:
        """
        Prune the choices after prescreening.
        """
        from .codegen.cutlass.kernel import CUTLASSTemplateCaller

        prescreen_key = f"{name}:{inputs_key}"

        # Check if we have cached postscreen results
        if prescreen_key in prescreen_cache:
            # candidate_timings are from choices that have won prescreening already
            winner_kernel_hashes = [
                candidate.kernel_hash_key() for candidate in candidate_timings
            ]

            pruned_choices = [
                choice
                for choice in choices
                if not isinstance(choice, CUTLASSTemplateCaller)
                or choice.kernel_hash_key() in winner_kernel_hashes
            ]
            return pruned_choices

        log.debug("Before pruning using prescreening timings, %d choices", len(choices))
        sorted_candidates = sorted(
            candidate_timings.keys(), key=lambda choice: candidate_timings[choice]
        )

        # Print prescreening timings
        if (
            candidate_timings
            and PRINT_AUTOTUNE
            and config.autotune_num_choices_displayed != 0
        ):
            n = config.autotune_num_choices_displayed
            top_k = sorted_candidates[:n]
            best = top_k[0]
            best_time = candidate_timings[best]

            lines = ["PRESCREENING CANDIDATE TIMINGS"]
            for choice in top_k:
                result = candidate_timings[choice]
                if result:
                    lines.append(
                        f"  {choice.name} {result:.4f} ms {best_time / result:.1%} {choice.description}"
                    )
                else:
                    lines.append(
                        f"  {choice.name} {result:.4f} ms <DIVIDED BY ZERO ERROR>"
                    )

            log.info("\n".join(lines))
        num_to_keep = max(int(math.sqrt(len(choices)) / 4), 8)

        # prune choices based on prescreening timings
        candidates_to_prune = OrderedSet(
            candidate.kernel_hash_key() for candidate in sorted_candidates[num_to_keep:]
        )
        winner_hashes: OrderedSet[str] = OrderedSet()
        for candidate in sorted_candidates[:num_to_keep]:
            if candidate_timings[candidate] == float("inf"):
                candidates_to_prune.add(candidate.kernel_hash_key())
            else:
                winner_hashes.add(candidate.hash_key())
                if isinstance(candidate, CUTLASSTemplateCaller):
                    candidate.bmreq.ensure_dll_loaded()

        pruned_choices = [
            choice
            for choice in choices
            if choice.kernel_hash_key() not in candidates_to_prune  # type: ignore[attr-defined]
        ]

        # Cache the hash_key of winners of prescreening
        prescreen_cache[prescreen_key] = winner_hashes

        log.debug(
            "After pruning using prescreening timings, %d choices", len(pruned_choices)
        )
        return pruned_choices