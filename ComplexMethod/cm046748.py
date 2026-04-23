def detect_vlm_dataset_structure(dataset):
    """
    Detects if VLM dataset is:
    - Standard VLM messages format (image objects in content)
    - Llava format (image indices + separate images column)
    - Simple format needing conversion (image + text columns)
    """
    try:
        sample = next(iter(dataset))
    except StopIteration:
        return {
            "format": "unknown",
            "needs_conversion": None,
            "image_column": None,
            "text_column": None,
            "messages_column": None,
        }

    column_names = set(sample.keys())

    # Check if has messages column
    if "messages" in column_names:
        messages = sample["messages"]

        if messages and len(messages) > 0:
            first_msg = messages[0]
            if "content" in first_msg:
                content = first_msg["content"]

                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and "type" in content[0]:
                        # Check for llava format
                        has_index = any(
                            "index" in item
                            for item in content
                            if isinstance(item, dict)
                        )
                        has_images_column = "images" in column_names

                        if has_index and has_images_column:
                            return {
                                "format": "vlm_messages_llava",
                                "needs_conversion": True,
                                "messages_column": "messages",
                                "image_column": "images",
                                "text_column": None,
                            }

                        # Standard VLM format
                        has_image = any(
                            "image" in item
                            for item in content
                            if isinstance(item, dict)
                        )
                        if has_image:
                            return {
                                "format": "vlm_messages",
                                "needs_conversion": False,
                                "messages_column": "messages",
                                "image_column": None,
                                "text_column": None,
                            }

    # Check for ShareGPT/ChatML conversations with <image> placeholder + companion image column
    # (e.g. Lin-Chen/ShareGPT4V, LLaVA-style datasets)
    for chat_col in ("conversations", "messages"):
        if chat_col not in column_names:
            continue
        chat_data = sample[chat_col]
        if not isinstance(chat_data, list) or len(chat_data) == 0:
            continue
        first_msg = chat_data[0]
        if not isinstance(first_msg, dict):
            continue
        # Detect ShareGPT (from/value) or ChatML (role/content) keys
        msg_text = first_msg.get("value") or first_msg.get("content")
        if not isinstance(msg_text, str):
            continue
        # Check for <image> placeholder anywhere in the conversation
        has_image_placeholder = any(
            "<image>" in str(m.get("value", "") or m.get("content", ""))
            for m in chat_data
            if isinstance(m, dict)
        )
        if not has_image_placeholder:
            continue
        # Find companion image column
        image_col = None
        for col in column_names:
            if col == chat_col:
                continue
            if _keyword_in_column("image", col) or _keyword_in_column("img", col):
                image_col = col
                break
        if image_col:
            return {
                "format": "sharegpt_with_images",
                "needs_conversion": True,
                "image_column": image_col,
                "text_column": None,
                "messages_column": chat_col,
            }

    # Find image and text columns using metadata filtering

    # Define metadata patterns to EXCLUDE
    metadata_patterns = {
        "suffixes": [
            "_id",
            "_url",
            "_name",
            "_filename",
            "_uri",
            "_link",
            "_key",
            "_index",
        ],
        "prefixes": [
            "id_",
            "url_",
            "name_",
            "filename_",
            "uri_",
            "link_",
            "key_",
            "index_",
        ],
    }

    # Image-related keywords
    image_keywords = [
        "image",
        "img",
        "photo",
        "picture",
        "pic",
        "visual",
        "scan",
        "file_name",
        "filename",
    ]

    # Text-related keywords
    text_keywords = [
        "text",
        "caption",
        "captions",
        "description",
        "answer",
        "output",
        "response",
        "label",
    ]

    def is_metadata_column(col_name):
        """Check if column name looks like metadata."""
        col_lower = col_name.lower()

        # Check suffixes
        if any(col_lower.endswith(suffix) for suffix in metadata_patterns["suffixes"]):
            return True

        # Check prefixes
        if any(
            col_lower.startswith(prefix) for prefix in metadata_patterns["prefixes"]
        ):
            return True

        return False

    def _score_image_candidate(col, sample_value):
        """Score a candidate image column by how resolvable its value is."""
        # PIL Image object (highest priority - already loaded)
        if hasattr(sample_value, "size") and hasattr(sample_value, "mode"):
            return 100

        # Dict with image data (bytes/path from HF Image feature)
        if isinstance(sample_value, dict) and (
            "bytes" in sample_value or "path" in sample_value
        ):
            return 75

        if isinstance(sample_value, str):
            # URL strings
            if sample_value.startswith(("http://", "https://")):
                return 70 if not is_metadata_column(col) else 55
            # Bare file path
            if is_metadata_column(col):
                return 30
            return 50

        return 0

    def _probe_image_candidate(col, sample_value):
        """Quick probe to check if an image candidate is actually reachable.
        Returns True if likely valid, False if definitely broken."""
        import os

        # PIL / dict — already loaded, always valid
        if not isinstance(sample_value, str):
            return True

        # Local file — check it exists
        if not sample_value.startswith(("http://", "https://")):
            return os.path.exists(
                sample_value
            )  # bare filenames return False here, that's OK

        # URL — quick HEAD request with short timeout
        try:
            import urllib.request

            req = urllib.request.Request(sample_value, method = "HEAD")
            resp = urllib.request.urlopen(req, timeout = 3)
            return resp.status < 400
        except Exception:
            return False

    def find_image_column():
        """Find image column by keyword match + value-based fallback.
        When multiple candidates exist, probes them to find one that works."""
        candidates = []

        # Pass 1: keyword-matched columns
        for col in column_names:
            if any(_keyword_in_column(keyword, col) for keyword in image_keywords):
                sample_value = sample[col]
                score = _score_image_candidate(col, sample_value)
                if score > 0:
                    candidates.append((col, score))

        # Pass 2: value-based fallback — find columns with image URLs/paths
        # even if the column name doesn't match image keywords
        already = {c[0] for c in candidates}
        for col in column_names:
            if col in already:
                continue
            sample_value = sample[col]
            if _is_image_value(sample_value):
                score = _score_image_candidate(col, sample_value)
                # Slightly penalise non-keyword columns so keyword matches win on ties
                candidates.append((col, max(score - 5, 1)))

        if not candidates:
            return None

        candidates.sort(key = lambda x: x[1], reverse = True)

        # Single candidate or top candidate is PIL/dict — no probing needed
        if len(candidates) == 1 or candidates[0][1] >= 75:
            return candidates[0][0]

        # Multiple string-based candidates — probe to find one that actually works
        for col, score in candidates:
            sample_value = sample[col]
            if _probe_image_candidate(col, sample_value):
                return col

        # Nothing probed successfully — return highest-scored anyway and let
        # conversion handle the error (it may still resolve via hf_hub_download)
        return candidates[0][0]

    def find_text_column():
        """Find text column by filtering out metadata and checking keywords."""
        candidates = []

        for col in column_names:
            # Skip metadata columns
            if is_metadata_column(col):
                continue

            # Check if contains text keywords (word-boundary match)
            if any(_keyword_in_column(keyword, col) for keyword in text_keywords):
                # Verify it's actually text
                sample_value = sample[col]

                if isinstance(sample_value, str) and len(sample_value) > 0:
                    # Longer text = higher priority (likely content, not just a label)
                    priority = min(len(sample_value), 1000)  # Cap at 1000
                    candidates.append((col, priority))
                elif (
                    isinstance(sample_value, list)
                    and len(sample_value) > 0
                    and isinstance(sample_value[0], str)
                ):
                    # List of strings (e.g. captions list) — lower priority than plain strings
                    priority = min(len(sample_value[0]), 1000) // 2
                    candidates.append((col, priority))

        # Return highest priority candidate
        if candidates:
            candidates.sort(key = lambda x: x[1], reverse = True)
            return candidates[0][0]

        return None

    found_image = find_image_column()
    found_text = find_text_column()

    if found_image and found_text:
        return {
            "format": "simple_image_text",
            "needs_conversion": True,
            "image_column": found_image,
            "text_column": found_text,
            "messages_column": None,
        }

    return {
        "format": "unknown",
        "needs_conversion": None,
        "image_column": found_image,
        "text_column": found_text,
        "messages_column": None,
    }