def check_ai_disclosure(pr_body):
    """Exactly one AI disclosure checkbox must be selected.

    If the "AI tools were used" option is checked, at least 5 words of
    additional description must be present in that section.
    """
    ai_match = re.search(
        r"#### AI Assistance Disclosure[^\n]*\n(.*?)(?=\r?\n####|\Z)",
        pr_body,
        re.DOTALL,
    )
    if not ai_match:
        return Message(*MISSING_AI_DISCLOSURE)

    section = strip_html_comments(ai_match.group(1))
    no_ai_checked = bool(
        re.search(r"-\s*\[x\].*?No AI tools were used", section, re.IGNORECASE)
    )
    ai_used_checked = bool(
        re.search(r"-\s*\[x\].*?If AI tools were used", section, re.IGNORECASE)
    )

    # Must check exactly one option.
    if no_ai_checked == ai_used_checked:
        return Message(*MISSING_AI_DISCLOSURE)

    if ai_used_checked:
        # Collect non-checkbox lines for word count.
        extra_lines = [
            line.strip()
            for line in section.splitlines()
            if line.strip() and not line.strip().startswith("- [")
        ]
        # Ensure PR author includes at least 5 words about their AI use.
        if len(" ".join(extra_lines).split()) < MIN_WORDS:
            return Message(*MISSING_AI_DESCRIPTION)

    return None