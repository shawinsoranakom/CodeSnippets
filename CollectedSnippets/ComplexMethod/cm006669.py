def validate_operations(self):
        """Ensure patch contains explicit and non-conflicting operations."""
        add_values = self.add_ids or []
        raw_values = self.add_raw_payloads or []
        remove_values = self.remove_ids or []

        if not add_values and not raw_values and not remove_values:
            msg = "At least one of 'add_ids', 'add_raw_payloads', or 'remove_ids' must be provided."
            raise ValueError(msg)

        # Overlap check covers add_ids vs remove_ids only.
        # add_raw_payloads carry flow-artifact IDs (Langflow domain),
        # while add_ids/remove_ids carry snapshot IDs (provider domain).
        overlap = set(add_values).intersection(remove_values)
        if overlap:
            ids = ", ".join(sorted(overlap))
            msg = f"Snapshot ids cannot be present in both 'add_ids' and 'remove_ids': {ids}."
            raise ValueError(msg)

        return self