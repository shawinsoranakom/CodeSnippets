def print_status(self):
        """Print GPU status in a compact table format using current stats."""
        self.refresh_stats()
        if not self.gpu_stats:
            LOGGER.warning("No GPU stats available.")
            return

        stats = self.gpu_stats
        name_len = max(len(gpu.get("name", "N/A")) for gpu in stats)
        hdr = f"{'Idx':<3} {'Name':<{name_len}} {'Util':>6} {'Mem (MiB)':>15} {'Temp':>5} {'Pwr (W)':>10}"
        LOGGER.info(f"\n--- GPU Status ---\n{hdr}\n{'-' * len(hdr)}")

        for gpu in stats:
            u = f"{gpu['utilization']:>5}%" if gpu["utilization"] >= 0 else " N/A "
            m = f"{gpu['memory_used']:>6}/{gpu['memory_total']:<6}" if gpu["memory_used"] >= 0 else " N/A / N/A "
            t = f"{gpu['temperature']}C" if gpu["temperature"] >= 0 else " N/A "
            p = f"{gpu['power_draw']:>3}/{gpu['power_limit']:<3}" if gpu["power_draw"] >= 0 else " N/A "

            LOGGER.info(f"{gpu.get('index'):<3d} {gpu.get('name', 'N/A'):<{name_len}} {u:>6} {m:>15} {t:>5} {p:>10}")

        LOGGER.info(f"{'-' * len(hdr)}\n")