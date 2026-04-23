def _optimize_selector(self, selector_str):
        """Optimize common selector patterns for better performance"""
        if not self.optimize_common_patterns:
            return selector_str

        # Handle td:nth-child(N) pattern which is very common in table scraping
        import re
        if re.search(r'td:nth-child\(\d+\)', selector_str):
            return selector_str  # Already handled specially in _apply_selector

        # Split complex selectors into parts for optimization
        parts = selector_str.split()
        if len(parts) <= 1:
            return selector_str

        # For very long selectors, consider using just the last specific part
        if len(parts) > 3 and any(p.startswith('.') or p.startswith('#') for p in parts):
            specific_parts = [p for p in parts if p.startswith('.') or p.startswith('#')]
            if specific_parts:
                return specific_parts[-1]  # Use most specific class/id selector

        return selector_str