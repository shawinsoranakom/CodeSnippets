def replace_placeholder(match):
        key = match.group(1)
        value = replacements.get(key, "")  # handle non defined placeholders
        if isinstance(value, datetime.datetime):
            return event_time_to_time_string(value)
        if isinstance(value, dict):
            json_str = to_json_str(value).replace('\\"', '"')
            if is_json_template:
                return json_str
            return json_str.replace('"', "")
        if isinstance(value, list):
            if is_json_template:
                return json.dumps(value)
            return f"[{','.join(value)}]"
        if isinstance(value, bool):
            return json.dumps(value)
        if is_nested_in_string(template, match):
            return value
        if is_json_template:
            return json.dumps(value)
        return value