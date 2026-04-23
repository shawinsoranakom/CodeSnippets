def find_block_ending(lines, start_idx, indent_level):
    end_idx = start_idx
    for idx, line in enumerate(lines[start_idx:]):
        indent = len(line) - len(line.lstrip())
        if idx == 0 or indent > indent_level or (indent == indent_level and line.strip() == ")"):
            end_idx = start_idx + idx
        elif idx > 0 and indent <= indent_level:
            # Outside the definition block of `pipeline_model_mapping`
            break

    return end_idx