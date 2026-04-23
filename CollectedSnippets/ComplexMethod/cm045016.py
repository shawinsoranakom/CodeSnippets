def _merge_vscode_settings(src: Path, dst: Path) -> None:
        """Merge settings from *src* into existing *dst* JSON file.

        Top-level keys from *src* are added only if missing in *dst*.
        For dict-valued keys, sub-keys are merged the same way.

        If *dst* cannot be parsed (e.g. JSONC with comments), the merge
        is skipped to avoid overwriting user settings.
        """
        try:
            existing = json.loads(dst.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Cannot parse existing file (likely JSONC with comments).
            # Skip merge to preserve the user's settings, but show
            # what they should add manually.
            import logging
            template_content = src.read_text(encoding="utf-8")
            logging.getLogger(__name__).warning(
                "Could not parse %s (may contain JSONC comments). "
                "Skipping settings merge to preserve existing file.\n"
                "Please add the following settings manually:\n%s",
                dst, template_content,
            )
            return

        new_settings = json.loads(src.read_text(encoding="utf-8"))

        if not isinstance(existing, dict) or not isinstance(new_settings, dict):
            import logging
            logging.getLogger(__name__).warning(
                "Skipping settings merge: %s or template is not a JSON object.", dst
            )
            return

        changed = False
        for key, value in new_settings.items():
            if key not in existing:
                existing[key] = value
                changed = True
            elif isinstance(existing[key], dict) and isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in existing[key]:
                        existing[key][sub_key] = sub_value
                        changed = True

        if not changed:
            return

        dst.write_text(
            json.dumps(existing, indent=4) + "\n", encoding="utf-8"
        )