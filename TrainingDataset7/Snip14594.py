def colorize(text="", opts=(), **kwargs):
    """
    Return your text, enclosed in ANSI graphics codes.

    Depends on the keyword arguments 'fg' and 'bg', and the contents of
    the opts tuple/list.

    Return the RESET code if no parameters are given.

    Valid colors:
        'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white'

    Valid options:
        'bold'
        'underscore'
        'blink'
        'reverse'
        'conceal'
        'noreset' - string will not be auto-terminated with the RESET code

    Examples:
        colorize('hello', fg='red', bg='blue', opts=('blink',))
        colorize()
        colorize('goodbye', opts=('underscore',))
        print(colorize('first line', fg='red', opts=('noreset',)))
        print('this should be red too')
        print(colorize('and so should this'))
        print('this should not be red')
    """
    code_list = []
    if text == "" and len(opts) == 1 and opts[0] == "reset":
        return "\x1b[%sm" % RESET
    for k, v in kwargs.items():
        if k == "fg":
            code_list.append(foreground[v])
        elif k == "bg":
            code_list.append(background[v])
    for o in opts:
        if o in opt_dict:
            code_list.append(opt_dict[o])
    if "noreset" not in opts:
        text = "%s\x1b[%sm" % (text or "", RESET)
    return "%s%s" % (("\x1b[%sm" % ";".join(code_list)), text or "")