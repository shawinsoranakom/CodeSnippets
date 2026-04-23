def randfill(fill):
    active = sorted(random.sample(range(5), random.randrange(6)))
    s = ''
    s += str(fill)
    s += random.choice('<>=^')
    for elem in active:
        if elem == 0: # sign
            s += random.choice('+- ')
        elif elem == 1: # width
            s += str(random.randrange(1, 100))
        elif elem == 2: # thousands separator
            s += ','
        elif elem == 3: # prec
            s += '.'
            s += str(random.randrange(100))
        elif elem == 4:
            if 2 in active: c = 'EeGgFf%'
            else: c = 'EeGgFfn%'
            s += random.choice(c)
    return s