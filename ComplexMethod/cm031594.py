def all_format_loc():
    for align in ('', '<', '>', '=', '^'):
        for fill in ('', 'x'):
            if align == '': fill = ''
            for sign in ('', '+', '-', ' '):
                for zeropad in ('', '0'):
                    if align != '': zeropad = ''
                    for width in ['']+[str(y) for y in range(1, 20)]+['101']:
                        for prec in ['']+['.'+str(y) for y in range(1, 20)]:
                            yield ''.join((fill, align, sign, zeropad, width, prec, 'n'))