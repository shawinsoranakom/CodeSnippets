def _is_valid_line(line: str) -> bool:
    """
    Check if a text line is valid content (not garbled)

    Multi-dimensional detection:
    1. Valid character ratio (Chinese, ASCII alphanumeric, common punctuation)
    2. Single-character spacing anomaly detection (PDF custom font mapping causing "O U W Z_W V 2" pattern)
    3. Consecutive meaningless alphanumeric sequence detection

    Args:
        line: Text line to check
    Returns:
        True means valid line, False means garbled line
    """
    if len(line) <= 3:
        # Short lines may be valid content like names, keep them
        return True

    cid_count = len(re.findall(r'\(cid:\d+\)', line))
    if cid_count >= 3:
        return False
    # Valid characters: Chinese (incl. extension), ASCII alphanumeric, common punctuation and spaces, fullwidth chars, CJK punctuation
    valid_chars = re.findall(
        r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff'
        r'a-zA-Z0-9\s@.,:;!?()（）【】\-_/\\|·•'
        r'、，。：；！？\u201c\u201d\u2018\u2019《》'
        r'\uff01-\uff5e'
        r'\u3000-\u303f'
        r'#%&+=~`\u00b7\u2022\u2013\u2014'
        r']',
        line
    )
    ratio = len(valid_chars) / len(line) if len(line) > 0 else 0
    if ratio < 0.5:
        return False

    # Detect PDF custom font mapping causing single-character spacing anomaly pattern
    # Feature: lots of "single letter space single letter space" sequences, e.g. "O U W Z_W V 2 X 3"
    # Stats: ratio of space-separated single chars among non-space chars
    spaced_singles = re.findall(r'(?:^|\s)([a-zA-Z0-9])(?:\s|$)', line)
    non_space_len = len(line.replace(" ", ""))
    if non_space_len > 5 and len(spaced_singles) > 0:
        # If ratio of space-separated single chars to non-space chars is too high, classify as garbled
        single_ratio = len(spaced_singles) / non_space_len
        if single_ratio > 0.3:
            return False

    # Detect consecutive meaningless mixed-case alphanumeric sequences (e.g. "UJqZX9V2")
    # Normal English words don't have such frequent case alternation patterns
    garbled_seqs = re.findall(r'[a-zA-Z0-9]{4,}', line.replace(" ", ""))
    if garbled_seqs:
        garbled_count = 0
        for seq in garbled_seqs:
            # Count case alternations
            case_changes = sum(
                1 for i in range(1, len(seq))
                if (seq[i].isupper() != seq[i-1].isupper() and seq[i].isalpha() and seq[i-1].isalpha())
                or (seq[i].isdigit() != seq[i-1].isdigit())
            )
            # Too high alternation frequency = garbled sequence (normal words like "Spring" have only 1 alternation)
            if len(seq) >= 4 and case_changes / len(seq) > 0.5:
                garbled_count += 1
        # If garbled sequence ratio is too high
        if len(garbled_seqs) > 0 and garbled_count / len(garbled_seqs) > 0.4:
            return False

    return True