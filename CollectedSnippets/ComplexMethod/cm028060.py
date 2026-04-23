def print_message(*xs):
    """print message fn."""
    _tf_print_counts[name] += 1
    if print_freq > 0:
      for i, x in enumerate(xs):
        _tf_print_running_sums[name][i] += x
      _tf_print_running_counts[name] += 1
    if (print_freq <= 0 or _tf_print_running_counts[name] >= print_freq) and (
        first_n < 0 or _tf_print_counts[name] <= first_n):
      for i, x in enumerate(xs):
        if print_freq > 0:
          del x
          x = _tf_print_running_sums[name][i]/_tf_print_running_counts[name]
        if sub_messages is None:
          sub_message = str(i)
        else:
          sub_message = sub_messages[i]
        log_message = "%s, %s" % (message, sub_message)
        if include_count:
          log_message += ", count=%d" % _tf_print_counts[name]
        tf.logging.info("[%s]: %s" % (log_message, x))
      if print_freq > 0:
        for i, x in enumerate(xs):
          _tf_print_running_sums[name][i] = 0
        _tf_print_running_counts[name] = 0
    return xs[0]