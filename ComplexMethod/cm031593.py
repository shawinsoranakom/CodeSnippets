def all_format_sep():
    for align in ('', '<', '>', '=', '^'):
        for fill in ('', 'x'):
            if align == '': fill = ''
            for sign in ('', '+', '-', ' '):
                for zeropad in ('', '0'):
                    if align != '': zeropad = ''
                    for width in ['']+[str(y) for y in range(1, 15)]+['101']:
                        for prec in ['']+['.'+str(y) for y in range(15)]:
                            # for type in ('', 'E', 'e', 'G', 'g', 'F', 'f', '%'):
                            type = random.choice(('', 'E', 'e', 'G', 'g', 'F', 'f', '%'))
                            yield ''.join((fill, align, sign, zeropad, width, ',', prec, type))