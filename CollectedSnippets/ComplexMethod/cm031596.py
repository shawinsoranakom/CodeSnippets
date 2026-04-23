def rand_locale():
    try:
        loc = random.choice(locale_list)
        locale.setlocale(locale.LC_ALL, loc)
    except locale.Error as err:
        pass
    active = sorted(random.sample(range(5), random.randrange(6)))
    s = ''
    have_align = 0
    for elem in active:
        if elem == 0: # fill+align
            s += chr(random.randrange(32, 128))
            s += random.choice('<>=^')
            have_align = 1
        elif elem == 1: # sign
            s += random.choice('+- ')
        elif elem == 2 and not have_align: # zeropad
            s += '0'
        elif elem == 3: # width
            s += str(random.randrange(1, 100))
        elif elem == 4: # prec
            s += '.'
            s += str(random.randrange(100))
    s += 'n'
    return s