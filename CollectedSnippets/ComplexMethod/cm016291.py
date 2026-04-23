def check_registry_sync(dynamo_dir: Path, registry_path: Path) -> list[LintMessage]:
    """Check registry sync and return lint messages."""
    lint_messages = []

    forbidden_raises = _collect_forbidden_unsupported_raises(dynamo_dir)
    for path, line, char in forbidden_raises:
        lint_messages.append(
            LintMessage(
                path=str(path),
                line=line,
                char=char,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="Direct raise Unsupported",
                original=None,
                replacement=None,
                description=(
                    "Do not directly `raise Unsupported(...)` in `torch/_dynamo`. "
                    "Use `unimplemented(...)` for graph breaks, or add `# noqa: GB_REGISTRY` "
                    "for infra-only exceptions."
                ),
            )
        )

    all_calls = _collect_all_calls(dynamo_dir)

    duplicates = []
    for gb_type, call_list in all_calls.items():
        if len(call_list) > 1:
            first_call = call_list[0][0]
            for call, file_path in call_list[1:]:
                if (
                    call["context"] != first_call["context"]
                    or call["explanation"] != first_call["explanation"]
                    or sorted(call["hints"]) != sorted(first_call["hints"])
                ):
                    duplicates.append({"gb_type": gb_type, "calls": call_list})
                    break

    for dup in duplicates:
        gb_type = dup["gb_type"]
        calls = dup["calls"]

        description = f"The gb_type '{gb_type}' is used {len(calls)} times with different content. "
        description += "Each gb_type must be unique across your entire codebase."

        lint_messages.append(
            LintMessage(
                path=str(calls[0][1]),
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.ERROR,
                name="Duplicate gb_type",
                original=None,
                replacement=None,
                description=description,
            )
        )

    if duplicates:
        return lint_messages

    calls = {gb_type: calls[0] for gb_type, calls in all_calls.items()}

    registry = load_registry(registry_path)

    # Check for duplicate gb_types across different GB IDs in the registry
    gb_type_to_ids: dict[str, list[str]] = {}
    for gb_id, entries in registry.items():
        gb_type = entries[0]["Gb_type"]
        if gb_type not in gb_type_to_ids:
            gb_type_to_ids[gb_type] = []
        gb_type_to_ids[gb_type].append(gb_id)

    duplicate_gb_types_in_registry = [
        (gb_type, ids) for gb_type, ids in gb_type_to_ids.items() if len(ids) > 1
    ]

    if duplicate_gb_types_in_registry:
        for gb_type, ids in duplicate_gb_types_in_registry:
            description = (
                f"The gb_type '{gb_type}' appears in multiple GB IDs: {', '.join(sorted(ids))}. "
                f"Each gb_type must map to exactly one GB ID. Please manually fix the registry."
            )
            lint_messages.append(
                LintMessage(
                    path=str(registry_path),
                    line=None,
                    char=None,
                    code=LINTER_CODE,
                    severity=LintSeverity.ERROR,
                    name="Duplicate gb_type in registry",
                    original=None,
                    replacement=None,
                    description=description,
                )
            )
        return lint_messages

    latest_entry: dict[str, Any] = {
        entries[0]["Gb_type"]: entries[0] for entries in registry.values()
    }

    renames: dict[str, str] = {}
    remaining_calls = dict(calls)

    for gb_type, (call, file_path) in calls.items():
        if gb_type not in latest_entry:
            for existing_gb_type, existing_entry in latest_entry.items():
                if (
                    call["context"] == existing_entry["Context"]
                    and call["explanation"] == existing_entry["Explanation"]
                    and sorted(call["hints"]) == sorted(existing_entry["Hints"])
                ):
                    renames[existing_gb_type] = gb_type
                    del remaining_calls[gb_type]
                    break

    needs_update = bool(renames)

    for gb_type, (call, file_path) in remaining_calls.items():
        if gb_type in latest_entry:
            existing_entry = latest_entry[gb_type]

            if not (
                call["context"] == existing_entry["Context"]
                and call["explanation"] == existing_entry["Explanation"]
                and sorted(call["hints"] or []) == sorted(existing_entry["Hints"] or [])
            ):
                needs_update = True
                break
        else:
            needs_update = True
            break

    if needs_update:
        updated_registry = _update_registry_with_changes(
            registry, remaining_calls, renames
        )

        original_content = registry_path.read_text(encoding="utf-8")

        replacement_content = (
            json.dumps(updated_registry, indent=2, ensure_ascii=False) + "\n"
        )

        changes = []
        if renames:
            for old, new in renames.items():
                changes.append(f"renamed '{old}' → '{new}'")
        if remaining_calls:
            new_count = sum(
                1 for gb_type in remaining_calls if gb_type not in latest_entry
            )
            if new_count:
                changes.append(f"added {new_count} new gb_types")

        description = f"Registry sync needed ({', '.join(changes)}). Run `lintrunner -a` to apply changes."

        lint_messages.append(
            LintMessage(
                path=str(registry_path),
                line=None,
                char=None,
                code=LINTER_CODE,
                severity=LintSeverity.WARNING,
                name="Registry sync needed",
                original=original_content,
                replacement=replacement_content,
                description=description,
            )
        )

    return lint_messages