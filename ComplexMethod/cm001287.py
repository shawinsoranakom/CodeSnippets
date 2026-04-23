def _detect_patterns(self, test: TestResult) -> list[FailurePattern]:
        """Detect failure patterns in a test result."""
        patterns = []

        # Pattern 1: Over-planning
        planning_tools = {"todo_write", "todo_read", "think", "plan"}
        execution_tools = {
            "write_file",
            "execute_python",
            "execute_shell",
            "read_file",
        }

        planning_count = sum(test.tool_distribution.get(t, 0) for t in planning_tools)
        _execution_count = sum(  # noqa: F841
            test.tool_distribution.get(t, 0) for t in execution_tools
        )

        if test.n_steps > 0:
            planning_ratio = planning_count / test.n_steps
            if planning_ratio > 0.5 and test.n_steps > 1:
                patterns.append(FailurePattern.OVER_PLANNING)

        # Pattern 2: Tool loops (same tool used 3+ times consecutively)
        if len(test.steps) >= 3:
            for i in range(len(test.steps) - 2):
                if (
                    test.steps[i].tool_name
                    == test.steps[i + 1].tool_name
                    == test.steps[i + 2].tool_name
                ):
                    patterns.append(FailurePattern.TOOL_LOOP)
                    break

        # Pattern 3: Missing critical action
        # If task mentions "write" or "create" but no write_file was used
        task_lower = test.task.lower()
        if any(word in task_lower for word in ["write", "create", "generate", "build"]):
            if test.tool_distribution.get("write_file", 0) == 0:
                patterns.append(FailurePattern.MISSING_CRITICAL)

        # Pattern 4: Timeout
        if test.reached_cutoff:
            patterns.append(FailurePattern.TIMEOUT)

        # Pattern 5: Error unrecovered
        error_count = 0
        for step in test.steps:
            if step.tool_result and step.tool_result.get("status") == "error":
                error_count += 1
        if error_count > 0 and error_count == len(test.steps) - 1:
            patterns.append(FailurePattern.ERROR_UNRECOVERED)

        if not patterns:
            patterns.append(FailurePattern.UNKNOWN)

        return patterns