def find_guarded_entry(
        cls: type[GuardedCache[T]],
        key: str,
        local: bool,
        remote_cache: RemoteCache[JsonDataTy] | None,
        evaluate_guards: Callable[[str, list[int] | list[torch.SymInt]], bool],
        hints: list[int],
    ) -> tuple[T | None, bytes | None, dict[str, str]]:
        """
        Find the first cache entry in iterate_over_candidates that passes `evaluate_guards`.

        Args:
            key: The cache key to look up
            local: Whether to check the local cache
            remote_cache: The remote cache to check, if any
            evaluate_guards: Function that evaluates whether a guard passes the check,
                given a list of hint values and the guard expression.
            hints: List of symint hints paired with evaluate_guards

        Returns:
            A tuple of (graph, pickled_content) if found, or (None, None) if not found
        """
        graph = None
        pickled_content = None
        result_status = "full_miss"
        sample_guards_expr = None
        in_local = False

        # Iterate over any entries in the subdir for this key and evaluate
        # guards to determine whether there's a hit.

        for candidate, content, in_local in cls.iterate_over_candidates(
            local, remote_cache, key
        ):
            assert hasattr(candidate, "guards_expr")
            if not candidate.guards_expr:  # type: ignore[attr-defined]
                # No guards to evaluate, so this is a hit.
                graph = candidate
                pickled_content = content
                result_status = "hit"
                break

            # Evaluate the guard expression in the current context.
            # If there's not a cache hit, we don't want the evaluation to
            # affect the current env, e.g., cause the creation of new guards,
            # so we evaluate with the hints instead of the symbols.
            hit = bool(evaluate_guards(candidate.guards_expr, hints))  # type: ignore[attr-defined]
            if hit:
                graph = candidate
                pickled_content = content
                result_status = "hit"
                sample_guards_expr = candidate.guards_expr
                break
            else:
                # At least one guard missed, log this
                result_status = "guard_miss"
                sample_guards_expr = candidate.guards_expr

        info = {"cache_status_detailed": result_status}
        if sample_guards_expr is not None:
            info["cache_status_guard_expr"] = sample_guards_expr

        # Record hits/misses for compilation event logging. The tricky part is that a
        # remote hit would imply a local miss (if local caching is enabled).
        local_hit = graph is not None and in_local
        remote_hit = graph is not None and not in_local
        local_miss = (graph is None or remote_hit) and local
        remote_miss = graph is None and remote_cache is not None
        cls._record_result(
            key,
            local_hit=local_hit,
            local_miss=local_miss,
            remote_hit=remote_hit,
            remote_miss=remote_miss,
        )

        return graph, pickled_content, info