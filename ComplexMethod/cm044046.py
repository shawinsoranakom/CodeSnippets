def _normalize_percent(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize percent values."""
        for k, v in data.items():
            if (
                k.endswith("Rate")
                or k.endswith("Yield")
                or k.endswith("Margin")
                or k.endswith("Percentage")
                or "spread" in k.lower()
            ):
                if v not in ["Yes", "No", None, ""]:
                    data[k] = float(v) / 100 if v else None
                else:
                    data[k] = v if v in ["Yes", "No"] else None
        return data