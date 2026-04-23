def _convert(examples):
        # Auto-detect which column name is used
        chatml_data = (
            examples.get("messages")
            or examples.get("conversations")
            or examples.get("texts")
        )

        if chatml_data is None:
            raise ValueError(
                "No 'messages' or 'conversations' or 'texts' column found."
            )

        instructions = []
        outputs = []
        inputs = []

        for convo in chatml_data:
            instruction = ""
            output = ""

            for msg in convo:
                # Handle both standard and ShareGPT formats
                role = msg.get("role") or msg.get("from")
                content = msg.get("content") or msg.get("value")

                # Get first user message as instruction
                if role in ["user", "human", "input"] and not instruction:
                    instruction = content
                # Get first assistant message as output
                elif role in ["assistant", "gpt", "output"] and not output:
                    output = content
                    break  # Stop after first assistant response

            instructions.append(instruction)
            inputs.append("")  # Alpaca typically has empty input
            outputs.append(output)

        return {"instruction": instructions, "input": inputs, "output": outputs}