def var_to_var(var_from: tf.Variable,
               var_to: tf.Variable,
               epsilon: float):
  """Expands a variable to another variable.

  Assuming the shape of `var_from` is (a, b, ..., y, z), then shape of `var_to`
  must be one of (a, ..., z * 2), (a * 2, ..., z * 2), or (a * 2, ..., z).

  If the shape of `var_to` is (a, ..., 2 * z):
    For any x, tf.matmul(x, var_to) ~= expand_vector(tf.matmul(x, var_from)) / 2
    Not that there will be noise added to the left hand side, if epsilon != 0.
  If the shape of `var_to` is (2 * a, ..., z):
    For any x, tf.matmul(expand_vector(x), var_to) == tf.matmul(x, var_from)
  If the shape of `var_to` is (2 * a, ..., 2 * z):
    For any x, tf.matmul(expand_vector(x), var_to) ==
        expand_vector(tf.matmul(expand_vector(x), var_from))

  Args:
    var_from: input variable to expand.
    var_to: output variable.
    epsilon: the noise ratio that will be added, when splitting `var_from`.
  """
  shape_from = var_from.shape
  shape_to = var_to.shape

  if shape_from == shape_to:
    var_to.assign(var_from)
    return

  var_from_np = var_from.numpy()

  if len(shape_from) == len(shape_to) == 1:
    var_to.assign(expand_vector(var_from_np))
    return

  a_from, z_from = shape_from[0], shape_from[-1]
  a_to, z_to = shape_to[0], shape_to[-1]

  if a_to == 2 * a_from and z_to == z_from:
    var_to.assign(expand_1_axis(var_from_np, epsilon=epsilon, axis=0))
    return

  if a_to == a_from and z_to == 2 * z_from:
    var_to.assign(expand_1_axis(var_from_np, epsilon=epsilon, axis=-1))
    return

  if a_to == 2 * a_from and z_to == 2 * z_from:
    var_to.assign(expand_2_axes(var_from_np, epsilon=epsilon))
    return

  raise ValueError("Shape not supported, {}, {}".format(shape_from, shape_to))