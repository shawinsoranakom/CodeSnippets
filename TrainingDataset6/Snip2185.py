def match(command):
    if 'not found' not in command.output:
        return False
    if any(u'ㄱ' <= ch <= u'ㅎ' or u'ㅏ' <= ch <= u'ㅣ' or u'가' <= ch <= u'힣'
            for ch in command.script):
        return True

    matched_layout = _get_matched_layout(command)
    return (matched_layout and
            _switch_command(command, matched_layout) != get_alias())