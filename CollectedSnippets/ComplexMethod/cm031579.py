def all_binary(prec, exp_range, itr):
    for a, b in bin_close_to_pow10(prec, exp_range, itr):
        yield a, b
    for a, b in bin_close_numbers(prec, exp_range, -exp_range, itr):
        yield a, b
    for a, b in bin_incr_digits(prec, exp_range, itr):
        yield a, b
    for a, b in bin_randfloat():
        yield a, b
    for a, b in bin_random_mixed_op(prec, exp_range, -exp_range, itr):
        yield a, b
    for a, b in logical_bin_incr_digits(prec, itr):
        yield a, b
    for _ in range(100):
        yield randdec(prec, exp_range), randdec(prec, exp_range)