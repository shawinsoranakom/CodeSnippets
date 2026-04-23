def _get_gpu_free_memory() -> list[tuple[int, int]]:
        """Query free memory per GPU via nvidia-smi.

        Returns list of (gpu_index, free_mib) sorted by index.
        Respects CUDA_VISIBLE_DEVICES if set.
        Returns empty list if nvidia-smi is not available.
        """
        import os

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,memory.free",
                    "--format=csv,noheader,nounits",
                ],
                capture_output = True,
                text = True,
                timeout = 10,
            )
            if result.returncode != 0:
                return []

            # Parse which GPUs are allowed by existing CUDA_VISIBLE_DEVICES
            allowed = None
            cvd = os.environ.get("CUDA_VISIBLE_DEVICES")
            if cvd is not None and cvd.strip():
                try:
                    allowed = set(int(x.strip()) for x in cvd.split(","))
                except ValueError:
                    pass  # Non-numeric (e.g., "GPU-uuid"), ignore filter

            gpus = []
            for line in result.stdout.strip().splitlines():
                parts = line.split(",")
                if len(parts) == 2:
                    idx = int(parts[0].strip())
                    free_mib = int(parts[1].strip())
                    if allowed is not None and idx not in allowed:
                        continue
                    gpus.append((idx, free_mib))
            return gpus
        except Exception as e:
            logger.debug(f"Failed to query GPU free memory via nvidia-smi: {e}")
            return []