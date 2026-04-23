def _extract_answer(self, result: ChallengeResult, environment: str) -> str:
        """Extract answer from agent output."""
        # Look for answer.txt
        for filename, content in result.output_files.items():
            if "answer" in filename.lower():
                return content.strip()

        # Environment-specific extraction
        if environment in ("db", "dbbench"):
            for filename, content in result.output_files.items():
                if filename.endswith(".sql"):
                    return content.strip()

        # Check if agent used finish command with an answer
        if result.steps:
            last_step = result.steps[-1]
            if last_step.tool_name == "finish":
                reason = last_step.tool_args.get("reason", "").strip()
                # Try to extract the actual answer from the finish reason
                # Often the answer is embedded in the reason
                if reason:
                    return reason

        # Look for potential answer in any text file output
        for filename, content in result.output_files.items():
            if filename.endswith(".txt") and content.strip():
                return content.strip()

        return ""