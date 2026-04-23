def _extract_expected_answer(self, environment: str, task: dict[str, Any]) -> str:
        """Extract the expected answer from task based on environment format."""
        # dbbench format: answer in "label" field (list)
        if environment == "dbbench":
            label = task.get("label", [])
            if isinstance(label, list) and label:
                return str(label[0])
            return str(label) if label else ""

        # knowledgegraph format: answer in "answer" array with entity_name
        if environment == "knowledgegraph":
            answers = task.get("answer", [])
            if isinstance(answers, list) and answers:
                first = answers[0]
                if isinstance(first, dict):
                    return first.get("entity_name", str(first))
                return str(first)
            return ""

        # lateralthinkingpuzzle format
        if environment == "lateralthinkingpuzzle":
            return task.get("answer", task.get("solution", ""))

        # Default: try common answer fields
        for key in ["answer", "expected", "gold", "label", "solution"]:
            val = task.get(key)
            if val:
                if isinstance(val, list):
                    return str(val[0]) if val else ""
                return str(val)
        return ""