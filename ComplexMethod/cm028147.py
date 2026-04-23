def init_linear(in_size, out_size, do_bias=True, mat_init_value=None,
                bias_init_value=None, alpha=1.0, identity_if_possible=False,
                normalized=False, name=None, collections=None, trainable=True):
  """Linear (affine) transformation, y = x W + b, for a variety of
  configurations.

  Args:
    in_size: The integer size of the non-batc input dimension. [(x),y]
    out_size: The integer size of non-batch output dimension. [x,(y)]
    do_bias (optional): Add a (learnable) bias vector to the operation,
      if false, b will be None
    mat_init_value (optional): numpy constant for matrix initialization, if None
      , do random, with additional parameters.
    alpha (optional): A multiplicative scaling for the weight initialization
      of the matrix, in the form \alpha * 1/\sqrt{x.shape[1]}.
    identity_if_possible (optional): just return identity,
      if x.shape[1] == out_size.
    normalized (optional): Option to divide out by the norms of the rows of W.
    name (optional): The name prefix to add to variables.
    collections (optional): List of additional collections. (Placed in
      tf.GraphKeys.GLOBAL_VARIABLES already, so no need for that.)

  Returns:
    In the equation, y = x W + b, returns the pair (W, b).
  """

  if mat_init_value is not None and mat_init_value.shape != (in_size, out_size):
    raise ValueError(
        'Provided mat_init_value must have shape [%d, %d].'%(in_size, out_size))
  if bias_init_value is not None and bias_init_value.shape != (1,out_size):
    raise ValueError(
        'Provided bias_init_value must have shape [1,%d].'%(out_size,))

  if mat_init_value is None:
    stddev = alpha/np.sqrt(float(in_size))
    mat_init = tf.random_normal_initializer(0.0, stddev)

  wname = (name + "/W") if name else "/W"

  if identity_if_possible and in_size == out_size:
    return (tf.constant(np.eye(in_size).astype(np.float32)),
            tf.zeros(in_size))

  # Note the use of get_variable vs. tf.Variable.  this is because get_variable
  # does not allow the initialization of the variable with a value.
  if normalized:
    w_collections = [tf.GraphKeys.GLOBAL_VARIABLES, "norm-variables"]
    if collections:
      w_collections += collections
    if mat_init_value is not None:
      w = tf.Variable(mat_init_value, name=wname, collections=w_collections,
                      trainable=trainable)
    else:
      w = tf.get_variable(wname, [in_size, out_size], initializer=mat_init,
                          collections=w_collections, trainable=trainable)
    w = tf.nn.l2_normalize(w, dim=0) # x W, so xW_j = \sum_i x_bi W_ij
  else:
    w_collections = [tf.GraphKeys.GLOBAL_VARIABLES]
    if collections:
      w_collections += collections
    if mat_init_value is not None:
      w = tf.Variable(mat_init_value, name=wname, collections=w_collections,
                      trainable=trainable)
    else:
      w = tf.get_variable(wname, [in_size, out_size], initializer=mat_init,
                          collections=w_collections, trainable=trainable)
  b = None
  if do_bias:
    b_collections = [tf.GraphKeys.GLOBAL_VARIABLES]
    if collections:
      b_collections += collections
    bname = (name + "/b") if name else "/b"
    if bias_init_value is None:
      b = tf.get_variable(bname, [1, out_size],
                          initializer=tf.zeros_initializer(),
                          collections=b_collections,
                          trainable=trainable)
    else:
      b = tf.Variable(bias_init_value, name=bname,
                      collections=b_collections,
                      trainable=trainable)

  return (w, b)