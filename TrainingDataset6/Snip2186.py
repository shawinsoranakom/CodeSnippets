def get_new_command(command):
    if any(u'ㄱ' <= ch <= u'ㅎ' or u'ㅏ' <= ch <= u'ㅣ' or u'가' <= ch <= u'힣'
            for ch in command.script):
        command.script = _decompose_korean(command)
    matched_layout = _get_matched_layout(command)
    return _switch_command(command, matched_layout)