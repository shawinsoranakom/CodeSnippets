def all_unary(prec, exp_range, itr):
    for a in un_close_to_pow10(prec, exp_range, itr):
        yield (a,)
    for a in un_close_numbers(prec, exp_range, -exp_range, itr):
        yield (a,)
    for a in un_incr_digits_tuple(prec, exp_range, itr):
        yield (a,)
    for a in un_randfloat():
        yield (a,)
    for a in un_random_mixed_op(itr):
        yield (a,)
    for a in logical_un_incr_digits(prec, itr):
        yield (a,)
    for _ in range(100):
        yield (randdec(prec, exp_range),)
    for _ in range(100):
        yield (randtuple(prec, exp_range),)