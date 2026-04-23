def format_text(text, f):
    '''
    @param f    String representation of formatting to apply in the form:
                [style] [light] font_color [on [light] bg_color]
                E.g. "red", "bold green on light blue"
    '''
    f = f.upper()
    tokens = f.strip().split()

    bg_color = ''
    if 'ON' in tokens:
        if tokens[-1] == 'ON':
            raise SyntaxError(f'Empty background format specified in {f!r}')
        if tokens[-1] not in _COLORS:
            raise SyntaxError(f'{tokens[-1]} in {f!r} must be a color')
        bg_color = f'4{_COLORS[tokens.pop()]}'
        if tokens[-1] == 'LIGHT':
            bg_color = f'0;10{bg_color[1:]}'
            tokens.pop()
        if tokens[-1] != 'ON':
            raise SyntaxError(f'Invalid format {f.split(" ON ", 1)[1]!r} in {f!r}')
        bg_color = f'\033[{bg_color}m'
        tokens.pop()

    if not tokens:
        fg_color = ''
    elif tokens[-1] not in _COLORS:
        raise SyntaxError(f'{tokens[-1]} in {f!r} must be a color')
    else:
        fg_color = f'3{_COLORS[tokens.pop()]}'
        if tokens and tokens[-1] == 'LIGHT':
            fg_color = f'9{fg_color[1:]}'
            tokens.pop()
        fg_style = tokens.pop() if tokens and tokens[-1] in _TEXT_STYLES else 'NORMAL'
        fg_color = f'\033[{_TEXT_STYLES[fg_style]};{fg_color}m'
        if tokens:
            raise SyntaxError(f'Invalid format {" ".join(tokens)!r} in {f!r}')

    if fg_color or bg_color:
        text = text.replace(CONTROL_SEQUENCES['RESET'], f'{fg_color}{bg_color}')
        return f'{fg_color}{bg_color}{text}{CONTROL_SEQUENCES["RESET"]}'
    else:
        return text