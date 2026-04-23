def format_script_for_slack(script_data) -> List[str]:
    if isinstance(script_data, dict):
        chunks = []
        current_chunk = ""
        title = script_data.get("title", "Podcast Script")
        current_chunk += f"*{title}*\n\n"
        sections = script_data.get("sections", [])
        for i, section in enumerate(sections):
            section_text = f"*Section {i + 1}: {section.get('type', 'Unknown').title()}*"
            if section.get("title"):
                section_text += f" - {section['title']}"
            section_text += "\n\n"
            if section.get("dialog"):
                for dialog in section["dialog"]:
                    speaker = dialog.get("speaker", "Speaker")
                    text = dialog.get("text", "")
                    dialog_text = f"*{speaker}:* {text}\n\n"
                    if len(current_chunk + section_text + dialog_text) > 3500:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = section_text + dialog_text
                    else:
                        current_chunk += section_text + dialog_text
                    section_text = ""
            else:
                current_chunk += section_text
            current_chunk += "\n---\n\n"
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks if chunks else ["Script content could not be formatted."]
    elif isinstance(script_data, str):
        try:
            parsed_data = json.loads(script_data)
            if isinstance(parsed_data, dict):
                return format_script_for_slack(parsed_data)
        except (json.JSONDecodeError, TypeError):
            pass
        text = script_data
        if len(text) <= 3500:
            return [text]
        else:
            return [text[i : i + 3500] for i in range(0, len(text), 3500)]
    else:
        try:
            text = str(script_data)
            if len(text) <= 3500:
                return [text]
            else:
                return [text[i : i + 3500] for i in range(0, len(text), 3500)]
        except Exception as e:
            print(f"Error converting script data to string: {e}")
            return ["Error: Could not format script data for display."]