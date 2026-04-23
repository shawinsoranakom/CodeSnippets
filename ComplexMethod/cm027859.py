def format_script_for_slack_snippet(script_data) -> str:
    if isinstance(script_data, dict):
        lines = []
        title = script_data.get("title", "Podcast Script")
        lines.append(f"PODCAST: {title}")
        lines.append("=" * (len(title) + 10))
        lines.append("")
        sections = script_data.get("sections", [])
        for i, section in enumerate(sections):
            section_type = section.get("type", "Unknown").upper()
            section_title = section.get("title", "")
            if section_title:
                lines.append(f"SECTION [{section_type}] {section_title}")
            else:
                lines.append(f"SECTION [{section_type}]")
            lines.append("-" * 50)
            lines.append("")
            if section.get("dialog"):
                for j, dialog in enumerate(section["dialog"]):
                    speaker = dialog.get("speaker", "SPEAKER")
                    text = dialog.get("text", "")
                    lines.append(f"SPEAKER {speaker}:")
                    if len(text) > 70:
                        words = text.split()
                        current_line = "   "
                        for word in words:
                            if len(current_line + word) > 70:
                                lines.append(current_line)
                                current_line = "   " + word
                            else:
                                current_line += " " + word if current_line != "   " else word
                        if current_line.strip():
                            lines.append(current_line)
                    else:
                        lines.append(f"   {text}")
                    lines.append("")
            if i < len(sections) - 1:
                lines.append("")
        return "\n".join(lines)
    return str(script_data) if script_data else "Script content not available"