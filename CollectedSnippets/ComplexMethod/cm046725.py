def llm_generate_vlm_instruction(
    column_names: list[str],
    samples: list[dict],
    dataset_name: Optional[str] = None,
) -> Optional[dict]:
    """
    Ask a helper LLM to generate a task-specific VLM instruction.

    Called when heuristic instruction generation returns low confidence
    or falls back to generic.

    Args:
        column_names: Column names in the dataset.
        samples: 3-5 sample rows with text values (images replaced by "<image>").
        dataset_name: Optional HF dataset identifier for context.

    Returns:
        {"instruction": str, "confidence": 0.85} or None.
    """
    # Format samples for the prompt
    formatted = ""
    for i, row in enumerate(samples[:5], 1):
        parts = []
        for col in column_names:
            val = str(row.get(col, ""))[:300]
            parts.append(f"  {col}: {val}")
        formatted += f"Sample {i}:\n" + "\n".join(parts) + "\n\n"

    prompt = (
        "You are a dataset analyst. Given a vision-language dataset, generate ONE "
        "instruction sentence that describes what the model should do with each image.\n\n"
        f"Dataset: {dataset_name or 'unknown'}\n"
        f"Columns: {column_names}\n\n"
        f"{formatted}"
        "Write ONE instruction sentence. Examples:\n"
        '- "Solve the math problem shown in the image and explain your reasoning."\n'
        '- "Transcribe all text visible in this image."\n'
        '- "Answer the question about this image."\n\n'
        "Respond with ONLY the instruction sentence, nothing else."
    )

    result = _run_with_helper(prompt, max_tokens = 100)
    if not result:
        return None

    # Clean up: strip quotes, ensure it's a single sentence
    instruction = result.strip().strip('"').strip("'").strip()
    # Reject obviously bad outputs (too short, too long, or multi-line)
    if len(instruction) < 10 or len(instruction) > 200 or "\n" in instruction:
        logger.warning(f"Helper model returned unusable instruction: {instruction!r}")
        return None

    logger.info(f"LLM-generated instruction: {instruction}")
    return {
        "instruction": instruction,
        "confidence": 0.85,
    }