def detect_custom_format_heuristic(dataset):
    """
    Smart detection with priority scoring.

    Strategy for ambiguous keywords like 'task':
    1. Detect assistant first (unambiguous)
    2. Detect user using high-priority keywords first
    3. Check REMAINING columns for system keywords (including 'task')
    4. Only if no system match, use 'task' as fallback user
    """
    sample = next(iter(dataset))
    all_columns = list(sample.keys())

    mapping = {}

    # Keywords
    assistant_words = [
        "output",
        "answer",
        "response",
        "assistant",
        "completion",
        "expected",
        "recommendation",
        "reply",
        "result",
        "target",
        "solution",
        "explanation",
        "solve",
    ]

    # Split into high/low priority
    user_words_high_priority = [
        "input",
        "question",
        "query",
        "prompt",
        "instruction",
        "request",
        "snippet",
        "user",
        "text",
        "problem",
        "exercise",
    ]
    user_words_low_priority = ["task"]  # Ambiguous - can be user OR system
    user_words = user_words_high_priority + user_words_low_priority

    system_words = [
        "system",
        "context",
        "description",
        "persona",
        "role",
        "template",
        "task",  # Also in system
    ]

    # Metadata columns to ignore
    metadata_exact_match = {
        "id",
        "idx",
        "index",
        "key",
        "timestamp",
        "date",
        "metadata",
        "source",
        "kind",
        "type",
        "category",
        "score",
        "label",
        "tag",
        "inference_mode",
    }

    metadata_prefix_patterns = [
        "problem_type",
        "problem_source",
        "generation_model",
        "pass_rate",
    ]

    priority_patterns = {
        "generated": 100,
        "gen_": 90,
        "model_": 80,
        "predicted": 70,
        "completion": 60,
    }

    def has_keyword(col_name, keywords):
        """Check if any keyword appears in column name."""
        col_lower = col_name.lower()
        col_normalized = col_lower.replace("_", "").replace("-", "").replace(" ", "")

        for keyword in keywords:
            if keyword in col_lower or keyword in col_normalized:
                return True
        return False

    def is_metadata(col_name):
        """Check if column is likely metadata."""
        col_lower = col_name.lower()

        if col_lower in metadata_exact_match:
            return True

        if col_lower in metadata_prefix_patterns:
            return True

        for pattern in metadata_prefix_patterns:
            if (
                col_lower.startswith(pattern.split("_")[0] + "_")
                and col_lower != pattern
            ):
                if "_" in col_lower:
                    prefix = col_lower.split("_")[0]
                    if prefix in ["generation", "pass", "inference"]:
                        return True

        if len(col_lower) <= 2 and not col_lower in ["qa", "q", "a"]:
            return True

        return False

    def get_priority_score(col_name):
        """Calculate priority score based on column name patterns."""
        col_lower = col_name.lower()
        score = 0

        for pattern, pattern_score in priority_patterns.items():
            if pattern in col_lower:
                score += pattern_score

        return score

    def get_content_length(col_name):
        """Get average content length for this column."""
        try:
            if col_name in sample and sample[col_name]:
                content = str(sample[col_name])
                return len(content)
            return 0
        except:
            return 0

    def score_column(col_name, keywords, role_type, num_candidates):
        """Score a column for how likely it is to be a particular role."""
        if not has_keyword(col_name, keywords):
            return 0

        score = 0
        score += 10

        # Penalize ambiguous keywords when scoring for user
        if role_type == "user":
            col_lower = col_name.lower()
            # If column is ONLY "task" (or task_xxx), give it lower priority for user role
            if "task" in col_lower and not any(
                kw in col_lower for kw in user_words_high_priority
            ):
                score -= 15  # Significant penalty so other user columns win

        priority_bonus = get_priority_score(col_name)
        score += priority_bonus

        if role_type in ["assistant", "user"]:
            avg_length = get_content_length(col_name)

            if num_candidates > 1:
                if avg_length > 1000:
                    score += 50
                elif avg_length > 200:
                    score += 30
                elif avg_length > 50:
                    score += 10
                elif avg_length < 50:
                    score -= 20
            else:
                if avg_length > 1000:
                    score += 50
                elif avg_length > 200:
                    score += 30
                elif avg_length > 50:
                    score += 10

        return score

    # Filter out metadata columns
    content_columns = [col for col in all_columns if not is_metadata(col)]

    # Count candidates first
    assistant_potential = [
        col for col in content_columns if has_keyword(col, assistant_words)
    ]
    user_potential = [col for col in content_columns if has_keyword(col, user_words)]

    # STEP 1: Find best ASSISTANT column
    assistant_candidates = []
    for col in assistant_potential:
        score = score_column(
            col, assistant_words, "assistant", len(assistant_potential)
        )
        if score > 0:
            assistant_candidates.append((col, score))

    if assistant_candidates:
        assistant_candidates.sort(key = lambda x: x[1], reverse = True)
        assistant_col = assistant_candidates[0][0]
        mapping[assistant_col] = "assistant"
    else:
        assistant_col = None

    # STEP 2: Find best USER column (with penalty for ambiguous keywords)
    user_candidates = []
    for col in user_potential:
        if col == assistant_col:
            continue
        score = score_column(col, user_words, "user", len(user_potential))
        if score > 0:
            user_candidates.append((col, score))

    if user_candidates:
        user_candidates.sort(key = lambda x: x[1], reverse = True)
        user_col = user_candidates[0][0]
        mapping[user_col] = "user"
    else:
        user_col = None

    # STEP 3: Check ALL remaining columns for SYSTEM matches (priority check)
    remaining_columns = [col for col in content_columns if col not in mapping]

    system_col = None
    for col in remaining_columns:
        if has_keyword(col, system_words):
            # Found a system match in remaining columns
            mapping[col] = "system"
            system_col = col
            break

    # STEP 4: Handle any additional remaining columns
    if system_col:
        remaining_columns = [col for col in remaining_columns if col != system_col]

    if len(remaining_columns) >= 1:
        remaining_col = remaining_columns[0]

        # If no strong keyword match, decide based on what's missing
        if not has_keyword(remaining_col, user_words + assistant_words):
            mapping[remaining_col] = "system"
        elif user_col is None:
            # No user column yet, assign this as user
            mapping[remaining_col] = "user"
        else:
            # Already have user + assistant, treat as system context
            mapping[remaining_col] = "system"

    # VALIDATION: Ensure we have at least user + assistant
    has_user = any(role == "user" for role in mapping.values())
    has_assistant = any(role == "assistant" for role in mapping.values())

    if not has_user and len(remaining_columns) > 0:
        for col in remaining_columns:
            if col not in mapping:
                mapping[col] = "user"
                has_user = True
                break

    if has_user and has_assistant:
        return mapping

    return None