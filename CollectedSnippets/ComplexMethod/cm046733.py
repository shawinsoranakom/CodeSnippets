def _apply_custom_mapping(examples):
                conversations = []
                num_examples = len(examples[list(examples.keys())[0]])

                # Only preserve unmapped columns if auto-detected
                preserved_columns = {}
                if not is_user_provided:
                    all_columns = set(examples.keys())
                    mapped_columns = set(custom_format_mapping.keys())
                    non_mapped_columns = all_columns - mapped_columns

                    for col in non_mapped_columns:
                        preserved_columns[col] = examples[col]

                for i in range(num_examples):
                    convo = []
                    role_order = ['system', 'user', 'assistant']

                    for target_role in role_order:
                        for col_name, role in custom_format_mapping.items():
                            if role == target_role and col_name in examples:
                                content = examples[col_name][i]

                                if is_user_provided:
                                    # User explicitly mapped - include even if empty
                                    convo.append({"role": role, "content": str(content) if content else ""})
                                else:
                                    # Auto-detected - skip empty
                                    if content and str(content).strip():
                                        convo.append({"role": role, "content": str(content)})

                    conversations.append(convo)

                result = {"conversations": conversations}
                if not is_user_provided:
                    result.update(preserved_columns)
                return result