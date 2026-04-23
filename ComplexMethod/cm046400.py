def _format_rate(self, rate: float) -> str:
        """Format rate with units, switching between it/s and s/it for readability."""
        if rate <= 0:
            return ""

        inv_rate = 1 / rate if rate else None

        # Use s/it format when inv_rate > 1 (i.e., rate < 1 it/s) for better readability
        if inv_rate and inv_rate > 1:
            return f"{inv_rate:.1f}s/B" if self.is_bytes else f"{inv_rate:.1f}s/{self.unit}"

        # Use it/s format for fast iterations
        fallback = f"{rate:.1f}B/s" if self.is_bytes else f"{rate:.1f}{self.unit}/s"
        return next((f"{rate / t:.1f}{u}" for t, u in self.scales if rate >= t), fallback)