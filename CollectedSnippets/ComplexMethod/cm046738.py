def format_dataset(
    dataset,
    format_type = "auto",
    tokenizer = None,
    aliases_for_system = [
        "system",
    ],
    aliases_for_user = [
        "user",
        "human",
        "input",
    ],
    aliases_for_assistant = [
        "gpt",
        "assistant",
        "output",
    ],
    batch_size = 1000,
    num_proc = None,
    auto_detect_custom = True,
    custom_format_mapping = None,
):
    """
    Formats dataset and returns metadata.

    Returns:
        dict: {
            "dataset": processed dataset,
            "detected_format": original format detected,
            "final_format": final format after processing,
            "chat_column": column name with chat data,
            "is_standardized": whether role names are standardized,
            "requires_manual_mapping": True if format detection failed and user must map columns,
            "warnings": list of warning messages
        }
    """

    # Detect multimodal first (needed for all flows)
    multimodal_info = detect_multimodal_dataset(dataset)

    # If user provided explicit mapping, skip detection and apply in the requested format
    if custom_format_mapping:
        try:
            if format_type == "alpaca":
                mapped_dataset = _apply_user_mapping_alpaca(
                    dataset, custom_format_mapping, batch_size
                )
                final_format = "alpaca"
                chat_column = None
            else:
                # auto / chatml / sharegpt / conversational — all produce chatml conversations
                # (sharegpt is always standardized to role/content internally)
                mapped_dataset = _apply_user_mapping(
                    dataset, custom_format_mapping, batch_size
                )
                final_format = "chatml_conversations"
                chat_column = "conversations"

            return {
                "dataset": mapped_dataset,
                "detected_format": "user_mapped",
                "final_format": final_format,
                "chat_column": chat_column,
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [
                    f"Applied user-provided column mapping ({format_type}): {custom_format_mapping}"
                ],
            }
        except Exception as e:
            return {
                "dataset": dataset,
                "detected_format": "user_mapped",
                "final_format": "unknown",
                "chat_column": None,
                "is_standardized": False,
                "requires_manual_mapping": True,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [f"Failed to apply user mapping: {e}"],
            }

    # Detect current format
    detected = detect_dataset_format(dataset)
    warnings = []

    # Add multimodal warning if detected
    if multimodal_info["is_image"]:
        warnings.append(
            f"Multimodal dataset detected. Found columns: {multimodal_info['multimodal_columns']}"
        )

    # AUTO MODE: Keep format but standardize if needed
    if format_type == "auto":
        # Alpaca - keep as is
        if detected["format"] == "alpaca":
            return {
                "dataset": dataset,
                "detected_format": "alpaca",
                "final_format": "alpaca",
                "chat_column": None,
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [],
            }

        # ShareGPT - needs standardization
        elif detected["format"] == "sharegpt":
            try:
                standardized = standardize_chat_format(
                    dataset,
                    tokenizer,
                    aliases_for_system,
                    aliases_for_user,
                    aliases_for_assistant,
                    batch_size,
                    num_proc,
                )
                return {
                    "dataset": standardized,
                    "detected_format": "sharegpt",
                    "final_format": f"chatml_{detected['chat_column']}",
                    "chat_column": detected["chat_column"],
                    "is_standardized": True,
                    "requires_manual_mapping": False,
                    "is_image": multimodal_info["is_image"],
                    "multimodal_info": multimodal_info,
                    "warnings": [],
                }
            except Exception as e:
                warnings.append(f"Failed to standardize ShareGPT format: {e}")
                return {
                    "dataset": dataset,
                    "detected_format": "sharegpt",
                    "final_format": "sharegpt",
                    "chat_column": detected["chat_column"],
                    "is_standardized": False,
                    "requires_manual_mapping": True,
                    "is_image": multimodal_info["is_image"],
                    "multimodal_info": multimodal_info,
                    "warnings": warnings,
                }

        elif detected["format"] == "chatml" and detected["chat_column"] in [
            "conversations",
            "messages",
            "texts",
        ]:
            return {
                "dataset": dataset,
                "detected_format": f"chatml_{detected['chat_column']}",
                "final_format": f"chatml_{detected['chat_column']}",
                "chat_column": detected["chat_column"],
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": warnings,
            }

        # Unknown - try standardization, if fails pass as is
        else:
            warnings.append(
                f"Unknown format detected. Keys found: {detected['sample_keys']}"
            )

            # NEW: Try heuristic detection
            if auto_detect_custom:
                custom_mapping = detect_custom_format_heuristic(dataset)
                if custom_mapping:
                    warnings.append(f"Auto-detected column mapping: {custom_mapping}")

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

                    try:
                        dataset = dataset.map(
                            _apply_auto_mapping, batched = True, batch_size = batch_size
                        )
                        return {
                            "dataset": dataset,
                            "detected_format": "unknown",
                            "final_format": "chatml_conversations",
                            "chat_column": "conversations",
                            "is_standardized": True,
                            "requires_manual_mapping": False,
                            "is_image": multimodal_info["is_image"],
                            "multimodal_info": multimodal_info,
                            "warnings": warnings,
                        }
                    except Exception as e:
                        warnings.append(f"Auto-detection failed: {e}")

            # Try standardization as a last resort
            if detected["chat_column"]:
                try:
                    standardized = standardize_chat_format(
                        dataset,
                        tokenizer,
                        aliases_for_system,
                        aliases_for_user,
                        aliases_for_assistant,
                        batch_size,
                        num_proc,
                    )
                    warnings.append("Successfully standardized unknown format")
                    return {
                        "dataset": standardized,
                        "detected_format": "unknown",
                        "final_format": f"chatml_{detected['chat_column']}",
                        "chat_column": detected["chat_column"],
                        "is_standardized": True,
                        "requires_manual_mapping": False,
                        "is_image": multimodal_info["is_image"],
                        "multimodal_info": multimodal_info,
                        "warnings": warnings,
                    }
                except Exception as e:
                    warnings.append(
                        f"Could not standardize: {e}. Passing dataset as-is."
                    )

            # Return as-is with warnings
            return {
                "dataset": dataset,
                "detected_format": "unknown",
                "final_format": "unknown",
                "chat_column": detected["chat_column"],
                "is_standardized": False,
                "requires_manual_mapping": True,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": warnings,
            }

    # ALPACA MODE: Convert to Alpaca
    elif format_type == "alpaca":
        if detected["format"] == "alpaca":
            return {
                "dataset": dataset,
                "detected_format": "alpaca",
                "final_format": "alpaca",
                "chat_column": None,
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [],
            }

        elif detected["format"] in ["sharegpt", "chatml"]:
            # First standardize if ShareGPT
            if detected["format"] == "sharegpt":
                dataset = standardize_chat_format(
                    dataset,
                    tokenizer,
                    aliases_for_system,
                    aliases_for_user,
                    aliases_for_assistant,
                    batch_size,
                    num_proc,
                )

            # Then convert to Alpaca
            converted = convert_chatml_to_alpaca(dataset, batch_size, num_proc)
            return {
                "dataset": converted,
                "detected_format": detected["format"],
                "final_format": "alpaca",
                "chat_column": None,
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [],
            }

        else:
            warnings.append(f"Cannot convert unknown format to Alpaca")
            return {
                "dataset": dataset,
                "detected_format": "unknown",
                "final_format": "unknown",
                "chat_column": detected["chat_column"],
                "is_standardized": False,
                "requires_manual_mapping": True,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": warnings,
            }

    # CHATML MODE: Convert to ChatML
    elif format_type in ["chatml", "conversational", "sharegpt"]:
        if detected["format"] == "alpaca":
            converted = convert_alpaca_to_chatml(dataset, batch_size, num_proc)
            return {
                "dataset": converted,
                "detected_format": "alpaca",
                "final_format": "chatml_conversations",
                "chat_column": "conversations",
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [],
            }

        elif detected["format"] == "sharegpt":
            standardized = standardize_chat_format(
                dataset,
                tokenizer,
                aliases_for_system,
                aliases_for_user,
                aliases_for_assistant,
                batch_size,
                num_proc,
            )
            return {
                "dataset": standardized,
                "detected_format": "sharegpt",
                "final_format": f"chatml_{detected['chat_column']}",
                "chat_column": detected["chat_column"],
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [],
            }

        elif detected["format"] == "chatml":
            return {
                "dataset": dataset,
                "detected_format": f"chatml_{detected['chat_column']}",
                "final_format": f"chatml_{detected['chat_column']}",
                "chat_column": detected["chat_column"],
                "is_standardized": True,
                "requires_manual_mapping": False,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": [],
            }

        else:
            warnings.append(f"Unknown format, attempting standardization")
            if detected["chat_column"]:
                try:
                    standardized = standardize_chat_format(
                        dataset,
                        tokenizer,
                        aliases_for_system,
                        aliases_for_user,
                        aliases_for_assistant,
                        batch_size,
                        num_proc,
                    )
                    return {
                        "dataset": standardized,
                        "detected_format": "unknown",
                        "final_format": f"chatml_{detected['chat_column']}",
                        "chat_column": detected["chat_column"],
                        "is_standardized": True,
                        "requires_manual_mapping": False,
                        "is_image": multimodal_info["is_image"],
                        "multimodal_info": multimodal_info,
                        "warnings": warnings,
                    }
                except Exception as e:
                    warnings.append(f"Standardization failed: {e}")

            return {
                "dataset": dataset,
                "detected_format": "unknown",
                "final_format": "unknown",
                "chat_column": detected["chat_column"],
                "is_standardized": False,
                "requires_manual_mapping": True,
                "is_image": multimodal_info["is_image"],
                "multimodal_info": multimodal_info,
                "warnings": warnings,
            }

    else:
        raise ValueError(f"Unknown format_type: {format_type}")