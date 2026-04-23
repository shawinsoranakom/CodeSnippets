def _eval_string_match(self, content: str, ground: dict) -> float:
        """Evaluate using string contains/not contains."""
        should_contain = ground.get("should_contain", [])
        should_not_contain = ground.get("should_not_contain", [])
        case_sensitive = ground.get("case_sensitive", True)

        check_content = content if case_sensitive else content.lower()

        # Check should_contain
        for phrase in should_contain:
            check_phrase = phrase if case_sensitive else phrase.lower()
            if check_phrase not in check_content:
                return 0.0

        # Check should_not_contain
        for phrase in should_not_contain:
            check_phrase = phrase if case_sensitive else phrase.lower()
            if check_phrase in check_content:
                return 0.0

        # All checks passed
        return 1.0