def _merge_new_deltas_to_single_response(self, initial_count: int) -> DeltaMessage:
        """
        Merge newly generated deltas from this processing
        into a single DeltaMessage

        Args:
            initial_count: Delta count before processing

        Returns:
            Merged DeltaMessage containing all newly generated delta information
        """
        if len(self.deltas) <= initial_count:
            return DeltaMessage(content=None)

        # Get newly generated deltas
        new_deltas = self.deltas[initial_count:]

        if len(new_deltas) == 1:
            # Only one new delta, return directly
            return new_deltas[0]

        # Merge multiple new deltas
        merged_tool_calls: list[DeltaToolCall] = []
        merged_content: str = ""

        for delta in new_deltas:
            if delta.content:
                merged_content += delta.content
            if delta.tool_calls:
                # For tool_calls, we need to intelligently merge arguments
                for tool_call in delta.tool_calls:
                    # Find if there's already a tool_call with the same call_id
                    existing_call = None
                    for existing in merged_tool_calls:
                        if existing.id == tool_call.id:
                            existing_call = existing
                            break

                    if existing_call and existing_call.function:
                        # Merge to existing tool_call
                        if tool_call.function and tool_call.function.name:
                            existing_call.function.name = tool_call.function.name
                        if (
                            tool_call.function
                            and tool_call.function.arguments is not None
                        ):
                            if existing_call.function.arguments is None:
                                existing_call.function.arguments = ""

                            # For streaming JSON parameters,
                            # simply concatenate in order
                            new_args = tool_call.function.arguments
                            existing_call.function.arguments += new_args
                        if tool_call.type:
                            existing_call.type = tool_call.type
                    else:
                        # Add new tool_call
                        merged_tool_calls.append(tool_call)

        return DeltaMessage(
            content=merged_content if merged_content else None,
            tool_calls=merged_tool_calls,
        )