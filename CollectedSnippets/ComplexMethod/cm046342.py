def select_idle_gpu(
        self, count: int = 1, min_memory_fraction: float = 0, min_util_fraction: float = 0
    ) -> list[int]:
        """Select the most idle GPUs based on utilization and free memory.

        Args:
            count (int): The number of idle GPUs to select.
            min_memory_fraction (float): Minimum free memory required as a fraction of total memory.
            min_util_fraction (float): Minimum free utilization rate required from 0.0 - 1.0.

        Returns:
            (list[int]): Indices of the selected GPUs, sorted by idleness (lowest utilization first).

        Notes:
             Returns fewer than 'count' if not enough qualify or exist.
             Returns empty list if NVML stats are unavailable or no GPUs meet the criteria.
        """
        assert min_memory_fraction <= 1.0, f"min_memory_fraction must be <= 1.0, got {min_memory_fraction}"
        assert min_util_fraction <= 1.0, f"min_util_fraction must be <= 1.0, got {min_util_fraction}"
        criteria = (
            f"free memory >= {min_memory_fraction * 100:.1f}% and free utilization >= {min_util_fraction * 100:.1f}%"
        )
        LOGGER.info(f"Searching for {count} idle GPUs with {criteria}...")

        if count <= 0:
            return []

        self.refresh_stats()
        if not self.gpu_stats:
            LOGGER.warning("NVML stats unavailable.")
            return []

        # Filter and sort eligible GPUs
        eligible_gpus = [
            gpu
            for gpu in self.gpu_stats
            if gpu.get("memory_free", 0) / gpu.get("memory_total", 1) >= min_memory_fraction
            and (100 - gpu.get("utilization", 100)) >= min_util_fraction * 100
        ]
        # Random tiebreaker prevents race conditions when multiple processes start simultaneously
        # and all GPUs appear equally idle (same utilization and free memory)
        eligible_gpus.sort(key=lambda x: (x.get("utilization", 101), -x.get("memory_free", 0), random.random()))

        # Select top 'count' indices
        selected = [gpu["index"] for gpu in eligible_gpus[:count]]

        if selected:
            if len(selected) < count:
                LOGGER.warning(f"Requested {count} GPUs but only {len(selected)} met the idle criteria.")
            LOGGER.info(f"Selected idle CUDA devices {selected}")
        else:
            LOGGER.warning(f"No GPUs met criteria ({criteria}).")

        return selected