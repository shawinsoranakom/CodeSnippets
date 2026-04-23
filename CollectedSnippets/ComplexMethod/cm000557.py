def get_missing_links(cls, data: BlockInput, links: list["Link"]) -> set[str]:
            # conversation_history & last_tool_output validation is handled differently
            missing_links = super().get_missing_links(
                data,
                [
                    link
                    for link in links
                    if link.sink_name
                    not in ["conversation_history", "last_tool_output"]
                ],
            )

            # Avoid executing the block if the last_tool_output is connected to a static
            # link, like StoreValueBlock or AgentInputBlock.
            if any(link.sink_name == "conversation_history" for link in links) and any(
                link.sink_name == "last_tool_output" and link.is_static
                for link in links
            ):
                raise ValueError(
                    "Last Tool Output can't be connected to a static (dashed line) "
                    "link like the output of `StoreValue` or `AgentInput` block"
                )

            # Check that both conversation_history and last_tool_output are connected together
            if any(link.sink_name == "conversation_history" for link in links) != any(
                link.sink_name == "last_tool_output" for link in links
            ):
                raise ValueError(
                    "Last Tool Output is needed when Conversation History is used, "
                    "and vice versa. Please connect both inputs together."
                )

            return missing_links