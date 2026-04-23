def _format_task(
        self, environment: str, description: str, task: dict[str, Any]
    ) -> str:
        """Format the task description based on environment."""
        if environment == "os":
            return (
                f"Operating System Task\n"
                f"=====================\n\n"
                f"{description}\n\n"
                f"You have access to a Linux command line. Execute commands "
                f"to complete the task. Save your final answer to 'answer.txt'."
            )

        elif environment in ("db", "dbbench"):
            # Extract table information from the task
            table_info = task.get("table", {})
            table_name = table_info.get("table_name", "data_table")
            columns_info = table_info.get("table_info", {}).get("columns", [])
            rows = table_info.get("table_info", {}).get("rows", [])

            # Format columns
            col_names = [col.get("name", "") for col in columns_info]

            # Build table display
            table_str_parts = [
                f"Table: {table_name}",
                f"Columns: {', '.join(col_names)}",
            ]
            table_str_parts.append("\nData (first 20 rows):")
            for i, row in enumerate(rows[:20]):
                row_str = " | ".join(str(cell) for cell in row)
                table_str_parts.append(f"  {i+1}. {row_str}")
            if len(rows) > 20:
                table_str_parts.append(f"  ... ({len(rows) - 20} more rows)")

            table_str = "\n".join(table_str_parts)

            return (
                f"Database Query Task\n"
                f"==================\n\n"
                f"Question: {description}\n\n"
                f"{table_str}\n\n"
                f"Analyze the table data above and answer the question. "
                f"Use the 'finish' command with your answer, or save your answer "
                f"to 'answer.txt'. Provide only the answer value, not an explanation."
            )

        elif environment == "kg":
            kg_info = task.get("kg_info", "")
            return (
                f"Knowledge Graph Task\n"
                f"====================\n\n"
                f"{description}\n\n"
                f"Knowledge Graph Information:\n{kg_info}\n\n"
                f"Reason over the knowledge graph to answer. "
                f"Save your answer to 'answer.txt'."
            )

        elif environment == "card_game":
            numbers = task.get("numbers", [])
            return (
                f"Card Game Task (24-point)\n"
                f"========================\n\n"
                f"Numbers: {numbers}\n\n"
                f"Use +, -, *, / and parentheses to make exactly 24. "
                f"Each number must be used exactly once.\n\n"
                f"Save your expression to 'answer.txt'."
            )

        elif environment == "ltp":
            return (
                f"Lateral Thinking Puzzle\n"
                f"======================\n\n"
                f"{description}\n\n"
                f"Ask yes/no questions to figure out the answer. "
                f"Save your final solution to 'answer.txt'."
            )

        elif environment in ("web_shopping", "web_browsing"):
            return (
                f"Web Task ({environment.replace('_', ' ').title()})\n"
                f"{'=' * 40}\n\n"
                f"{description}\n\n"
                f"Navigate the web to complete the task. "
                f"Save your final answer to 'answer.txt'."
            )

        elif environment == "alfworld":
            return (
                f"ALFWorld Task\n"
                f"=============\n\n"
                f"{description}\n\n"
                f"Navigate and interact with the environment to complete the task. "
                f"Use available actions to achieve the goal."
            )

        else:
            return description