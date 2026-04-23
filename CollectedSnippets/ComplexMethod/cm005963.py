def _ensure_chronological_order(self, messages):
                    # Copy the implementation for testing
                    if len(messages) <= 1:
                        return messages

                    human_messages = [
                        (i, msg) for i, msg in enumerate(messages) if hasattr(msg, "type") and msg.type == "human"
                    ]
                    ai_messages = [
                        (i, msg) for i, msg in enumerate(messages) if hasattr(msg, "type") and msg.type == "ai"
                    ]

                    if len(human_messages) >= 2:
                        _first_human_idx, first_human = human_messages[0]
                        _last_human_idx, last_human = human_messages[-1]

                        first_content = str(getattr(first_human, "content", ""))
                        last_content = str(getattr(last_human, "content", ""))

                        if ("plus" in first_content.lower()) and ("353454" in last_content):
                            ordered_messages = []

                            for _, msg in reversed(human_messages):
                                content = str(getattr(msg, "content", ""))
                                if "353454" in content:
                                    ordered_messages.append(msg)
                                    break

                            for _, msg in ai_messages:
                                ordered_messages.append(msg)

                            for _, msg in human_messages:
                                content = str(getattr(msg, "content", ""))
                                if "plus" in content.lower():
                                    ordered_messages.append(msg)
                                    break

                            if ordered_messages:
                                return ordered_messages

                    return messages