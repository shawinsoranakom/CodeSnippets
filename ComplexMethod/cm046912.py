def validate_dataset(self, dataset):
        """
        Check for:
        - Minimum/maximum sequence lengths
        - Character encoding issues
        - Repeated content
        - Empty chunks
        """
        stats = {
            "total_samples": len(dataset),
            "empty_samples": 0,
            "min_length": float("inf"),
            "max_length": 0,
            "avg_length": 0,
            "repeated_content": 0,
            "encoding_issues": 0,
            "warnings": [],
        }

        texts = dataset["text"]
        text_lengths = []
        seen_texts = set()

        for i, text in enumerate(texts):
            if not text or len(text.strip()) == 0:
                stats["empty_samples"] += 1
                continue

            # Check for encoding issues
            try:
                text.encode("utf-8")
            except UnicodeEncodeError:
                stats["encoding_issues"] += 1

            # Calculate lengths
            length = len(text)
            text_lengths.append(length)
            stats["min_length"] = min(stats["min_length"], length)
            stats["max_length"] = max(stats["max_length"], length)

            # Check for repeated content
            text_hash = hash(text.strip())
            if text_hash in seen_texts:
                stats["repeated_content"] += 1
            else:
                seen_texts.add(text_hash)

        # Calculate average length
        if text_lengths:
            stats["avg_length"] = sum(text_lengths) / len(text_lengths)
            stats["min_length"] = (
                stats["min_length"] if stats["min_length"] != float("inf") else 0
            )

        # Generate warnings
        if stats["empty_samples"] > 0:
            stats["warnings"].append(f"Found {stats['empty_samples']} empty samples")

        if stats["repeated_content"] > 0:
            stats["warnings"].append(
                f"Found {stats['repeated_content']} repeated samples"
            )

        if stats["encoding_issues"] > 0:
            stats["warnings"].append(
                f"Found {stats['encoding_issues']} encoding issues"
            )

        if stats["min_length"] < 10:
            stats["warnings"].append("Some samples are very short (< 10 characters)")

        return stats