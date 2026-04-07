def _line_at_position(content, position):
            start = content.rfind("\n", 0, position) + 1
            end = content.find("\n", position)
            end = end if end != -1 else len(content)
            line_num = content.count("\n", 0, start) + 1
            msg = f"\n{line_num}: {content[start:end]}"
            if len(msg) > 79:
                return f"\n{line_num}"
            return msg