def test_method(method, testspecs, testfunc):
    """Iterate a test function through many context settings."""
    log("testing %s ...", method)
    stat = defaultdict(int)
    for spec in testspecs:
        if 'samples' in spec:
            spec['prec'] = sorted(random.sample(range(1, 101),
                                  spec['samples']))
        for prec in spec['prec']:
            context.prec = prec
            for expts in spec['expts']:
                emin, emax = expts
                if emin == 'rand':
                    context.Emin = random.randrange(-1000, 0)
                    context.Emax = random.randrange(prec, 1000)
                else:
                    context.Emin, context.Emax = emin, emax
                if prec > context.Emax: continue
                log("    prec: %d  emin: %d  emax: %d",
                    (context.prec, context.Emin, context.Emax))
                restr_range = 9999 if context.Emax > 9999 else context.Emax+99
                for rounding in RoundModes:
                    context.rounding = rounding
                    context.capitals = random.randrange(2)
                    if spec['clamp'] == 'rand':
                        context.clamp = random.randrange(2)
                    else:
                        context.clamp = spec['clamp']
                    exprange = context.c.Emax
                    testfunc(method, prec, exprange, restr_range,
                             spec['iter'], stat)
    log("    result types: %s" % sorted([t for t in stat.items()]))