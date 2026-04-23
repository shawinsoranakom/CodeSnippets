def rand_format(fill, typespec='EeGgFfn%'):
    active = sorted(random.sample(range(7), random.randrange(8)))
    have_align = 0
    s = ''
    for elem in active:
        if elem == 0: # fill+align
            s += fill
            s += random.choice('<>=^')
            have_align = 1
        elif elem == 1: # sign
            s += random.choice('+- ')
        elif elem == 2 and not have_align: # zeropad
            s += '0'
        elif elem == 3: # width
            s += str(random.randrange(1, 100))
        elif elem == 4: # thousands separator
            s += ','
        elif elem == 5: # prec
            s += '.'
            s += str(random.randrange(100))
        elif elem == 6:
            if 4 in active: c = typespec.replace('n', '')
            else: c = typespec
            s += random.choice(c)
    return s