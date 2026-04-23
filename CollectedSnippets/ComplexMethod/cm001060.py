def fix_double_curly_braces(self, agent: AgentDict) -> AgentDict:
        """
        Fix single curly braces to double curly braces in nodes with prompt or
        format fields. Also ensures that prompt_values (passed via links) are
        referenced in the prompt/format. Skips fixing if the block's output will
        be passed to a CodeExecutionBlock.

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """

        nodes = agent.get("nodes", [])
        links = agent.get("links", [])

        # Build a map of node_id -> list of prompt_value names that are linked
        node_prompt_values: dict[str, list[str]] = {}
        for link in links:
            sink_id = link.get("sink_id")
            sink_name = link.get("sink_name", "")

            # Check if this link is passing a prompt_value
            if sink_name == "prompt_values":
                # Direct prompt_values link
                if sink_id not in node_prompt_values:
                    node_prompt_values[sink_id] = []
                # We don't have a specific name for this, skip for now
            elif sink_name.startswith("prompt_values_"):
                # Extract value name from pattern: prompt_values_#_[value_name]
                after_prefix = sink_name[len("prompt_values_") :]
                first_underscore_idx = after_prefix.find("_")
                if first_underscore_idx != -1:
                    value_name = after_prefix[first_underscore_idx + 1 :]
                    if sink_id not in node_prompt_values:
                        node_prompt_values[sink_id] = []
                    node_prompt_values[sink_id].append(value_name)

        # Process nodes that have prompt or format fields
        for node in nodes:
            node_id = node.get("id")
            input_data = node.get("input_default", {})

            # Check if this node has prompt or format fields
            has_prompt_or_format = "prompt" in input_data or "format" in input_data

            if not has_prompt_or_format:
                continue

            # Check if this block's output is linked to a CodeExecutionBlock
            is_linked_to_code_execution = False
            for link in links:
                if link.get("source_id") == node_id:
                    sink_node = next(
                        (n for n in nodes if n.get("id") == link.get("sink_id")),
                        None,
                    )
                    if (
                        sink_node
                        and sink_node.get("block_id") == _CODE_EXECUTION_BLOCK_ID
                    ):
                        is_linked_to_code_execution = True
                        break

            # Skip fixing if this block's output goes to a CodeExecutionBlock
            if is_linked_to_code_execution:
                continue

            # Fix single curly braces to double curly braces
            for key in ("prompt", "format"):
                if key in input_data:
                    original_text = input_data[key]
                    if not isinstance(original_text, str):
                        continue

                    # Avoid fixing already double-braced values
                    fixed_text = re.sub(
                        r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})",
                        r"{{\1}}",
                        original_text,
                    )

                    if fixed_text != original_text:
                        input_data[key] = fixed_text
                        self.add_fix_log(
                            f"Fixed {key} in node {node_id}: "
                            f"{original_text} -> {fixed_text}"
                        )

            # Check if this node has prompt_values linked to it
            if node_id in node_prompt_values:
                prompt_values = node_prompt_values[node_id]

                # Determine which field to add missing values to
                target_field = "prompt" if "prompt" in input_data else "format"

                if target_field in input_data and isinstance(
                    input_data[target_field], str
                ):
                    current_text = input_data[target_field]
                    missing_values = []

                    for value_name in prompt_values:
                        pattern = r"\{\{" + re.escape(value_name) + r"\}\}"
                        if not re.search(pattern, current_text):
                            missing_values.append(value_name)

                    # Add missing values to the text
                    if missing_values:
                        additions = "\n".join(
                            [f"{{{{{value_name}}}}}" for value_name in missing_values]
                        )
                        updated_text = current_text + "\n" + additions
                        input_data[target_field] = updated_text
                        self.add_fix_log(
                            f"Added missing prompt_values to {target_field} "
                            f"in node {node_id}: {missing_values}"
                        )

        return agent