def _convert(examples):
        num = len(next(iter(examples.values())))
        conversations = []
        for i in range(num):
            convo = []

            # System prompt (generated, static across all rows)
            if system_prompt:
                convo.append({"role": "system", "content": system_prompt})

            # User message: concatenate all user-role column values
            user_parts = []
            for col in role_groups["user"]:
                if col in examples:
                    user_parts.append(
                        _extract_column_value(examples[col][i], col, label_mapping)
                    )
            if user_parts:
                convo.append({"role": "user", "content": "\n".join(user_parts)})

            # Assistant message: concatenate all assistant-role column values
            asst_parts = []
            for col in role_groups["assistant"]:
                if col in examples:
                    asst_parts.append(
                        _extract_column_value(examples[col][i], col, label_mapping)
                    )
            if asst_parts:
                convo.append({"role": "assistant", "content": "\n".join(asst_parts)})

            conversations.append(convo)
        return {"conversations": conversations}