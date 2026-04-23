def test_load_model_stage_ordering(self):
        """Stages appear in the expected order."""
        _, events = self._load_model(self.MODEL)

        stages = [e["stage"] for e in events if e["status"] == "loading" and "stage" in e]
        seen = set()
        unique_stages = []
        for s in stages:
            if s not in seen:
                seen.add(s)
                unique_stages.append(s)

        expected_order = ["processor", "config", "download", "weights"]
        expected_present = [s for s in expected_order if s in unique_stages]
        self.assertEqual(unique_stages, expected_present, "Stages appeared out of order")