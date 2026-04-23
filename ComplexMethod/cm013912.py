def generate_pstats(
        self, output_file: str | None = None, print_raw: bool = False
    ) -> pstats.Stats:
        """Generate pstats.Stats object from recorded timings.

        Args:
            output_file: Optional file path to save the stats.
            print_raw: If True, print raw aggregate timings before returning.
        """
        import cProfile
        import io
        import logging
        import pstats

        log = logging.getLogger(__name__)

        # Aggregate by (filename, lineno, func_name)
        aggregated: dict[tuple[str, int, str], dict[str, Any]] = {}
        # caller_edges[callee_key][caller_key] -> edge stats
        caller_edges: dict[
            tuple[str, int, str], dict[tuple[str, int, str], dict[str, Any]]
        ] = {}

        for t in self.timings:
            key = (t.filename, t.firstlineno, t.func_name)

            if key not in aggregated:
                aggregated[key] = {
                    "ncalls": 0,
                    "pcalls": 0,
                    "tottime": 0.0,
                    "cumtime": 0.0,
                }
                caller_edges[key] = {}

            agg = aggregated[key]
            agg["ncalls"] += 1
            agg["tottime"] += t.tottime_ns / 1e9

            if t.is_primitive_call:
                agg["pcalls"] += 1
                agg["cumtime"] += t.cumtime_ns / 1e9

            # Build caller edge
            if t.caller_filename is not None:
                caller_key = (
                    t.caller_filename,
                    t.caller_firstlineno or 0,
                    t.caller_func_name or "",
                )
                if caller_key not in caller_edges[key]:
                    caller_edges[key][caller_key] = {
                        "ncalls": 0,
                        "pcalls": 0,
                        "tottime": 0.0,
                        "cumtime": 0.0,
                    }
                edge = caller_edges[key][caller_key]
                edge["ncalls"] += 1
                edge["tottime"] += t.tottime_ns / 1e9
                # Always add cumtime to edges for visualization (gprof2dot)
                # Function-level cumtime is already correct (only primitive calls)
                edge["cumtime"] += t.cumtime_ns / 1e9
                if t.is_primitive_call:
                    edge["pcalls"] += 1

        if print_raw:
            sorted_items = sorted(
                aggregated.items(), key=lambda x: x[1]["cumtime"], reverse=True
            )
            print("\n=== Aggregate Timings (raw) ===")
            print(
                f"{'ncalls':>8} {'pcalls':>8} {'tottime':>12} {'cumtime':>12}  function"
            )
            print("-" * 80)
            total_cumtime = 0.0
            total_tottime = 0.0
            for (filename, lineno, func_name), agg in sorted_items:
                ncalls = agg["ncalls"]
                pcalls = agg["pcalls"]
                tottime = agg["tottime"] * 1000  # convert to ms
                cumtime = agg["cumtime"] * 1000
                total_cumtime += cumtime
                total_tottime += tottime
                short_file = filename.split("/")[-1] if "/" in filename else filename
                print(
                    f"{ncalls:>8} {pcalls:>8} {tottime:>10.2f}ms {cumtime:>10.2f}ms  "
                    f"{func_name} ({short_file}:{lineno})"
                )
            print("-" * 80)
            print(
                f"Total timings: {len(self.timings)}, unique functions: {len(aggregated)}"
            )
            print(
                f"Sum tottime: {total_tottime:.2f}ms, Sum cumtime: {total_cumtime:.2f}ms"
            )

        # Ensure caller-only functions have a top-level entry.
        # gprof2dot expects every function referenced as a caller to also
        # exist as a top-level entry in the stats dict with timing data.
        for key in list(caller_edges.keys()):
            for caller_key in caller_edges[key]:
                if caller_key not in aggregated:
                    aggregated[caller_key] = {
                        "ncalls": 0,
                        "pcalls": 0,
                        "tottime": 0.0,
                        "cumtime": 0.0,
                    }
                    caller_edges[caller_key] = {}

        # Build the stats dict in pstats format
        stats_dict: dict[
            tuple[str, int, str], tuple[int, int, float, float, dict[Any, Any]]
        ] = {}

        for key, agg in aggregated.items():
            callers: dict[tuple[str, int, str], tuple[int, int, float, float]] = {}
            for caller_key, edge in caller_edges[key].items():
                callers[caller_key] = (
                    edge["ncalls"],
                    edge["pcalls"],
                    edge["tottime"],
                    edge["cumtime"],
                )

            stats_dict[key] = (
                agg["pcalls"],
                agg["ncalls"],
                agg["tottime"],
                agg["cumtime"],
                callers,
            )

        # Create a pstats.Stats object
        dummy_profile = cProfile.Profile()
        dummy_profile.enable()
        dummy_profile.disable()
        stats = pstats.Stats(dummy_profile, stream=io.StringIO())

        stats.stats = stats_dict  # type: ignore[attr-defined]
        stats.total_calls = sum(s[1] for s in stats_dict.values())  # type: ignore[attr-defined]
        stats.prim_calls = sum(s[0] for s in stats_dict.values())  # type: ignore[attr-defined]
        stats.total_tt = sum(s[2] for s in stats_dict.values())  # type: ignore[attr-defined]

        if output_file:
            stats.dump_stats(output_file)
            log.info(
                "Saved pstats to %s. Visualize with: snakeviz %s",
                output_file,
                output_file,
            )

        return stats