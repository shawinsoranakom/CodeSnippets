def vectorize(grads_and_vars, set_none_to_zero=False, skip_none=False):
  if set_none_to_zero:
    return tf.concat([tf.reshape(g, [-1]) if g is not None else
                         tf.reshape(tf.zeros_like(v), [-1]) for g, v in grads_and_vars], 0)
  elif skip_none:
    return tf.concat([tf.reshape(g, [-1]) for g, v in grads_and_vars if g is not None], 0)
  else:
    return tf.concat([tf.reshape(g, [-1]) for g, v in grads_and_vars], 0)