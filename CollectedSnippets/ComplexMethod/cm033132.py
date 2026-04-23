def is_jsonl_format(self, txt: str, sample_limit: int = 10, threshold: float = 0.8) -> bool:
        lines = [line.strip() for line in txt.strip().splitlines() if line.strip()]
        if not lines:
            return False

        try:
            json.loads(txt)
            return False
        except json.JSONDecodeError:
            pass

        sample_limit = min(len(lines), sample_limit)
        sample_lines = lines[:sample_limit]
        valid_lines = sum(1 for line in sample_lines if self._is_valid_json(line))

        if not valid_lines:
            return False

        return (valid_lines / len(sample_lines)) >= threshold