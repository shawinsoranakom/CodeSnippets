def main():
    try:
        data = json.load(sys.stdin)
        debug_log(f"Hook invoked with data: {json.dumps(data, indent=2)}")
        tool_input = data.get("tool_input", {})

        requested_labels = tool_input.get("labels", []) or []
        debug_log(f"Labels requested: {requested_labels}")

        if not requested_labels:
            debug_log("No labels provided, allowing")
            sys.exit(0)

        owner = tool_input.get("owner", "pytorch")
        repo = tool_input.get("repo", "pytorch")
        issue_number = tool_input.get("issue_number")
        if not issue_number:
            raise RuntimeError("tool_input missing issue_number")

        forbidden = [l for l in requested_labels if is_forbidden(l)]
        clean_labels = [l for l in requested_labels if not is_forbidden(l)]

        if forbidden:
            debug_log(f"Stripped forbidden labels: {forbidden}")
            if not clean_labels:
                clean_labels = ["triage review"]
            elif "triage review" not in clean_labels:
                clean_labels.append("triage review")
            print(
                f"Stripped forbidden labels (require human decision): {forbidden}. "
                f"Added 'triage review' for human attention.",
                file=sys.stderr,
            )

        valid_labels = load_valid_labels()
        nonexistent = [l for l in clean_labels if l not in valid_labels]
        clean_labels = [l for l in clean_labels if l in valid_labels]

        if nonexistent:
            debug_log(f"Stripped non-existent labels: {nonexistent}")
            print(
                f"Stripped non-existent labels: {nonexistent}",
                file=sys.stderr,
            )

        clean_labels, removed_redundant = strip_redundant(clean_labels)
        if removed_redundant:
            debug_log(f"Stripped redundant labels: {removed_redundant}")
            print(
                f"Stripped redundant labels: {removed_redundant}",
                file=sys.stderr,
            )

        if not clean_labels:
            debug_log("No valid labels remain after filtering, blocking")
            print(
                "All requested labels were invalid. No labels to apply.",
                file=sys.stderr,
            )
            sys.exit(2)

        existing_labels = fetch_existing_labels(owner, repo, issue_number)
        debug_log(f"Existing labels on issue: {existing_labels}")

        merged = sorted(set(existing_labels) | set(clean_labels))
        debug_log(f"Merged labels (existing + new): {merged}")

        allow_with_updated_input(tool_input, merged)

    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        print(f"Hook error: Invalid JSON input: {e}", file=sys.stderr)
        print(
            "Hook was unable to validate labels; stopping triage.",
            file=sys.stderr,
        )
        sys.exit(2)
    except Exception as e:
        debug_log(f"Unexpected error: {type(e).__name__}: {e}")
        print(f"Hook error: {e}", file=sys.stderr)
        print(
            "Hook was unable to validate labels; stopping triage.",
            file=sys.stderr,
        )
        sys.exit(2)