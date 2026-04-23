def format_and_template_dataset(
    dataset,
    model_name,
    tokenizer,
    is_vlm = False,
    format_type = "auto",
    # VLM-specific parameters
    vlm_instruction = None,  # Now optional - will auto-generate
    vlm_text_column = None,
    vlm_image_column = None,
    dataset_name = None,
    custom_prompt_template = None,
    add_eos_token = False,
    remove_bos_prefix = False,
    custom_format_mapping = None,
    auto_detect_custom = True,
    auto_detect_mapping = True,
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
    progress_callback = None,
):
    """
    Convenience function that combines format_dataset and apply_chat_template_to_dataset.
    Perfect for UI workflows - one function does everything!

    Returns:
        dict: {
            "dataset": Final dataset with 'text' column,
            "detected_format": Original format,
            "final_format": Format after processing,
            "success": Whether template application succeeded,
            "requires_manual_mapping": True if format detection failed and user must map columns,
            "warnings": List of warnings,
            "errors": List of errors,
            "summary": Human-readable summary
        }
    """

    # VLM FLOW
    if is_vlm:
        warnings = []
        errors = []

        multimodal_info = detect_multimodal_dataset(dataset)

        # NEW: If user provided explicit mapping for VLM, use it directly
        if custom_format_mapping:
            # Expect mapping like: {"image_col": "image", "caption_col": "text"}
            user_vlm_image_column = None
            user_vlm_text_column = None

            for col, role in custom_format_mapping.items():
                if role == "image":
                    user_vlm_image_column = col
                elif role in ["text", "user", "caption", "assistant"]:
                    user_vlm_text_column = col

            if user_vlm_image_column and user_vlm_text_column:
                try:
                    dataset = convert_to_vlm_format(
                        dataset,
                        instruction = vlm_instruction,
                        text_column = user_vlm_text_column,
                        image_column = user_vlm_image_column,
                        dataset_name = dataset_name,
                        progress_callback = progress_callback,
                    )
                    warnings.append(
                        f"Applied user VLM mapping: image='{user_vlm_image_column}', text='{user_vlm_text_column}'"
                    )

                    return {
                        "dataset": dataset,
                        "detected_format": "user_mapped",
                        "final_format": "vlm_messages",
                        "chat_column": "messages",
                        "is_vlm": True,
                        "is_image": True,
                        "multimodal_info": multimodal_info,
                        "success": True,
                        "requires_manual_mapping": False,
                        "warnings": warnings,
                        "errors": [],
                    }
                except Exception as e:
                    # User mapping failed — fall back to auto-detection instead
                    # of giving up (handles stale cached mappings gracefully)
                    warnings.append(
                        f"User VLM mapping (image='{user_vlm_image_column}', "
                        f"text='{user_vlm_text_column}') failed: {e} — "
                        f"falling back to auto-detection"
                    )
                    logger.info(
                        f"⚠️ User VLM mapping failed, falling back to auto-detection..."
                    )
                    custom_format_mapping = None  # clear so auto-detection runs below
            else:
                errors.append(
                    f"Invalid VLM mapping: need 'image' and 'text' roles. Got: {custom_format_mapping}"
                )
                return {
                    "dataset": dataset,
                    "detected_format": "user_mapped",
                    "final_format": "vlm_unknown",
                    "is_vlm": True,
                    "success": False,
                    "requires_manual_mapping": True,
                    "warnings": warnings,
                    "errors": errors,
                }

        # Auto-detect VLM structure
        vlm_structure = detect_vlm_dataset_structure(dataset)

        # Handle Llava format
        if vlm_structure["format"] == "vlm_messages_llava":
            try:
                dataset = convert_llava_to_vlm_format(dataset)
                warnings.append(
                    "Converted from Llava format (image indices) to standard VLM format"
                )
            except Exception as e:
                errors.append(f"Failed to convert Llava format: {e}")
                import traceback

                traceback.print_exc()

                return {
                    "dataset": dataset,
                    "detected_format": "vlm_messages_llava",
                    "final_format": "vlm_conversion_failed",
                    "is_vlm": True,
                    "success": False,
                    "requires_manual_mapping": True,
                    "warnings": warnings,
                    "errors": errors,
                }

        # Handle ShareGPT/ChatML + image column (e.g. ShareGPT4V, LLaVA-style)
        elif vlm_structure["format"] == "sharegpt_with_images":
            try:
                dataset = convert_sharegpt_with_images_to_vlm_format(
                    dataset,
                    image_column = vlm_structure["image_column"],
                    messages_column = vlm_structure["messages_column"],
                    dataset_name = dataset_name,
                    progress_callback = progress_callback,
                )
                warnings.append(
                    "Converted from ShareGPT+image format to standard VLM format"
                )
            except Exception as e:
                errors.append(f"Failed to convert ShareGPT+image format: {e}")
                import traceback

                traceback.print_exc()

                return {
                    "dataset": dataset,
                    "detected_format": "sharegpt_with_images",
                    "final_format": "vlm_conversion_failed",
                    "is_vlm": True,
                    "success": False,
                    "requires_manual_mapping": True,
                    "warnings": warnings,
                    "errors": errors,
                }

        # Handle simple format
        elif vlm_structure["needs_conversion"]:
            if vlm_text_column is None:
                vlm_text_column = vlm_structure["text_column"]
            if vlm_image_column is None:
                vlm_image_column = vlm_structure["image_column"]

            if vlm_text_column is None or vlm_image_column is None:
                columns = list(next(iter(dataset)).keys()) if dataset else []
                issues = [
                    f"Could not auto-detect image and text columns from: {columns}",
                    f"VLM structure detected: {vlm_structure.get('format', 'unknown')}",
                ]
                friendly = None
                try:
                    from .llm_assist import llm_generate_dataset_warning

                    friendly = llm_generate_dataset_warning(
                        issues,
                        dataset_name = dataset_name,
                        modality = "vision",
                        column_names = columns,
                    )
                except Exception:
                    pass
                errors.append(
                    friendly
                    or f"Could not auto-detect image/text columns. Found: {vlm_structure}. "
                )
                return {
                    "dataset": dataset,
                    "detected_format": "vlm_unknown",
                    "final_format": "vlm_unknown",
                    "is_vlm": True,
                    "success": False,
                    "requires_manual_mapping": True,
                    "warnings": warnings,
                    "errors": errors,
                }

            try:
                dataset = convert_to_vlm_format(
                    dataset,
                    instruction = vlm_instruction,
                    text_column = vlm_text_column,
                    image_column = vlm_image_column,
                    dataset_name = dataset_name,
                    progress_callback = progress_callback,
                )

                if vlm_instruction:
                    warnings.append(
                        f"Using user-provided instruction: '{vlm_instruction}'"
                    )
                else:
                    warnings.append(
                        "Auto-generated instruction based on dataset analysis"
                    )

            except Exception as e:
                errors.append(f"Failed to convert to VLM format: {e}")
                import traceback

                traceback.print_exc()

                return {
                    "dataset": dataset,
                    "detected_format": vlm_structure["format"],
                    "final_format": "vlm_conversion_failed",
                    "is_vlm": True,
                    "success": False,
                    "requires_manual_mapping": True,
                    "warnings": warnings,
                    "errors": errors,
                }

        # Already in standard VLM format
        elif vlm_structure["format"] == "vlm_messages":
            dataset = [sample for sample in dataset]
            warnings.append("Dataset already in standard VLM messages format")

        # Return as list
        return {
            "dataset": dataset,
            "detected_format": vlm_structure["format"],
            "final_format": "vlm_messages",
            "chat_column": "messages",
            "is_vlm": True,
            "is_image": multimodal_info["is_image"],
            "multimodal_info": multimodal_info,
            "vlm_structure": vlm_structure,
            "success": True,
            "requires_manual_mapping": False,
            "warnings": warnings,
            "errors": errors,
        }

    # LLM FLOW (Existing code)
    else:
        # Step 1: Format the dataset
        n_rows = len(dataset) if hasattr(dataset, "__len__") else None
        if progress_callback and n_rows:
            progress_callback(status_message = f"Formatting dataset ({n_rows:,} rows)...")
        dataset_info = format_dataset(
            dataset,
            format_type = format_type,
            tokenizer = tokenizer,
            auto_detect_custom = auto_detect_custom,
            custom_format_mapping = custom_format_mapping,
            aliases_for_system = aliases_for_system,
            aliases_for_user = aliases_for_user,
            aliases_for_assistant = aliases_for_assistant,
            batch_size = batch_size,
            num_proc = num_proc,
        )

        # Step 2: Apply chat template
        detected = dataset_info.get("detected_format", "unknown")
        if progress_callback and n_rows:
            progress_callback(
                status_message = f"Applying chat template to {detected} ({n_rows:,} rows)..."
            )
        # Gemma emits a leading <bos> that must be stripped for text-only chatml/sharegpt.
        is_alpaca = format_type == "alpaca" or (
            format_type == "auto" and dataset_info["detected_format"] == "alpaca"
        )
        is_gemma = "gemma" in model_name.lower()
        if is_gemma and not dataset_info["is_image"] and not is_alpaca:
            remove_bos_prefix = True
        template_result = apply_chat_template_to_dataset(
            dataset_info = dataset_info,
            tokenizer = tokenizer,
            model_name = model_name,
            custom_prompt_template = custom_prompt_template,
            add_eos_token = add_eos_token,
            remove_bos_prefix = remove_bos_prefix,
            custom_format_mapping = custom_format_mapping,
            auto_detect_mapping = auto_detect_mapping,
            batch_size = batch_size,
            num_proc = num_proc,
            progress_callback = progress_callback,
        )

        # Step 3: Generate summary
        summary = get_dataset_info_summary(dataset_info)

        # Combine results
        all_warnings = dataset_info.get("warnings", []) + template_result.get(
            "warnings", []
        )
        all_errors = template_result.get("errors", [])

        # If format_dataset returned "unknown" but apply_chat_template rescued
        # it via heuristic detection, update final_format to reflect reality.
        final_format = dataset_info["final_format"]
        requires_manual = dataset_info.get("requires_manual_mapping", False)
        if final_format == "unknown" and template_result["success"]:
            out_ds = template_result["dataset"]
            if hasattr(out_ds, "column_names") and "text" in out_ds.column_names:
                final_format = "chatml_conversations"
                requires_manual = False

        return {
            "dataset": template_result["dataset"],
            "detected_format": dataset_info["detected_format"],
            "final_format": final_format,
            "chat_column": dataset_info.get("chat_column"),
            "is_vlm": False,  # This is LLM flow
            "success": template_result["success"],
            "requires_manual_mapping": requires_manual,
            "warnings": all_warnings,
            "errors": all_errors,
            "summary": summary,
        }