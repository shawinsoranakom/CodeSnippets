def _apply_auto_mapping(examples):
                        conversations = []
                        num_examples = len(examples[list(examples.keys())[0]])

                        # Preserve non-mapped columns
                        all_columns = set(examples.keys())
                        mapped_columns = set(custom_mapping.keys())
                        preserved_columns = {
                            col: examples[col] for col in all_columns - mapped_columns
                        }

                        for i in range(num_examples):
                            convo = []
                            for target_role in ["system", "user", "assistant"]:
                                for col_name, role in custom_mapping.items():
                                    if role == target_role and col_name in examples:
                                        content = examples[col_name][i]
                                        if content and str(content).strip():
                                            convo.append(
                                                {"role": role, "content": str(content)}
                                            )
                            conversations.append(convo)

                        return {"conversations": conversations, **preserved_columns}