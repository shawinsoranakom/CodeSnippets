def _print_unwinder_stats(self):
        """Print unwinder statistics including cache performance."""
        try:
            stats = self.unwinder.get_stats()
        except RuntimeError:
            return  # Stats not enabled

        print(f"\n{ANSIColors.BOLD_BLUE}{'='*50}{ANSIColors.RESET}")
        print(f"{ANSIColors.BOLD_BLUE}Unwinder Statistics:{ANSIColors.RESET}")

        # Frame cache stats
        total_samples = stats.get('total_samples', 0)
        frame_cache_hits = stats.get('frame_cache_hits', 0)
        frame_cache_partial_hits = stats.get('frame_cache_partial_hits', 0)
        frame_cache_misses = stats.get('frame_cache_misses', 0)
        total_lookups = frame_cache_hits + frame_cache_partial_hits + frame_cache_misses

        # Calculate percentages
        hits_pct = (frame_cache_hits / total_lookups * 100) if total_lookups > 0 else 0
        partial_pct = (frame_cache_partial_hits / total_lookups * 100) if total_lookups > 0 else 0
        misses_pct = (frame_cache_misses / total_lookups * 100) if total_lookups > 0 else 0

        print(f"  {ANSIColors.CYAN}Frame Cache:{ANSIColors.RESET}")
        print(f"    Total samples:    {total_samples:n}")
        print(f"    Full hits:        {frame_cache_hits:n} ({ANSIColors.GREEN}{fmt(hits_pct)}%{ANSIColors.RESET})")
        print(f"    Partial hits:     {frame_cache_partial_hits:n} ({ANSIColors.YELLOW}{fmt(partial_pct)}%{ANSIColors.RESET})")
        print(f"    Misses:           {frame_cache_misses:n} ({ANSIColors.RED}{fmt(misses_pct)}%{ANSIColors.RESET})")

        # Frame read stats
        frames_from_cache = stats.get('frames_read_from_cache', 0)
        frames_from_memory = stats.get('frames_read_from_memory', 0)
        total_frames = frames_from_cache + frames_from_memory
        cache_frame_pct = (frames_from_cache / total_frames * 100) if total_frames > 0 else 0
        memory_frame_pct = (frames_from_memory / total_frames * 100) if total_frames > 0 else 0

        print(f"  {ANSIColors.CYAN}Frame Reads:{ANSIColors.RESET}")
        print(f"    From cache:       {frames_from_cache:n} ({ANSIColors.GREEN}{fmt(cache_frame_pct)}%{ANSIColors.RESET})")
        print(f"    From memory:      {frames_from_memory:n} ({ANSIColors.RED}{fmt(memory_frame_pct)}%{ANSIColors.RESET})")

        # Code object cache stats
        code_hits = stats.get('code_object_cache_hits', 0)
        code_misses = stats.get('code_object_cache_misses', 0)
        total_code = code_hits + code_misses
        code_hits_pct = (code_hits / total_code * 100) if total_code > 0 else 0
        code_misses_pct = (code_misses / total_code * 100) if total_code > 0 else 0

        print(f"  {ANSIColors.CYAN}Code Object Cache:{ANSIColors.RESET}")
        print(f"    Hits:             {code_hits:n} ({ANSIColors.GREEN}{fmt(code_hits_pct)}%{ANSIColors.RESET})")
        print(f"    Misses:           {code_misses:n} ({ANSIColors.RED}{fmt(code_misses_pct)}%{ANSIColors.RESET})")

        # Memory operations
        memory_reads = stats.get('memory_reads', 0)
        memory_bytes = stats.get('memory_bytes_read', 0)
        if memory_bytes >= 1024 * 1024:
            memory_str = f"{fmt(memory_bytes / (1024 * 1024))} MB"
        elif memory_bytes >= 1024:
            memory_str = f"{fmt(memory_bytes / 1024)} KB"
        else:
            memory_str = f"{memory_bytes} B"
        print(f"  {ANSIColors.CYAN}Memory:{ANSIColors.RESET}")
        print(f"    Read operations:  {memory_reads:n} ({memory_str})")

        # Stale invalidations
        stale_invalidations = stats.get('stale_cache_invalidations', 0)
        if stale_invalidations > 0:
            print(f"  {ANSIColors.YELLOW}Stale cache invalidations: {stale_invalidations}{ANSIColors.RESET}")