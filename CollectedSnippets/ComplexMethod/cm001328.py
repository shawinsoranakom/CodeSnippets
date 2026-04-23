def _process_generation(self, content: str) -> None:
        """Process the generation phase response."""
        # Initialize tree if needed
        if not self.tree:
            self.tree = ThoughtTree(root_content="Initial problem analysis")

        # Try to extract candidates from response
        # Look for JSON array of candidates
        try:
            # Try to find array in response
            array_match = re.search(r"\[.*\]", content, re.DOTALL)
            if array_match:
                candidates_data = json.loads(array_match.group())
                self.pending_candidates = [
                    ThoughtCandidate(
                        thought=c.get("thought", c.get("reasoning", "")),
                        leads_to_action=c.get("leads_to_action", False),
                        action_name=c.get("action_name"),
                        action_arguments=c.get("action_arguments"),
                    )
                    for c in candidates_data
                    if isinstance(c, dict)
                ]
        except (json.JSONDecodeError, ValueError):
            # Fallback: extract thoughts from numbered list
            pattern = re.compile(r"(\d+)\.\s+(.+?)(?=\n\d+\.|\n*$)", re.DOTALL)
            matches = pattern.findall(content)
            self.pending_candidates = [
                ThoughtCandidate(thought=match[1].strip())
                for match in matches[: self.config.branching_factor]
            ]

        if self.pending_candidates:
            self.tree.add_candidates(self.pending_candidates)