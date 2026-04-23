def _einsum_flops(graph, node):
  """Calculates the compute resources needed for Einsum."""
  assert len(node.input) == 2
  x_shape = tf.compat.v1.graph_util.tensor_shape_from_node_def_name(
      graph, node.input[0])
  y_shape = tf.compat.v1.graph_util.tensor_shape_from_node_def_name(
      graph, node.input[1])
  x_shape.assert_is_fully_defined()
  y_shape.assert_is_fully_defined()
  x_shape = x_shape.as_list()
  y_shape = y_shape.as_list()
  equation = str(node.attr['equation'])
  equation = (
      equation.replace('s:', '')
      .replace('"', '')
      .replace(' ', '')
      .replace('\n', '')
  )
  x_str = equation.split(',')[0]
  y_r_str = equation.split(',')[1]
  y_str = y_r_str.split('->')[0]
  r_str = y_r_str.split('->')[1]
  shape_dic = {}
  contracted = set()
  for indice in x_str + y_str:
    if indice in x_str:
      indice_dim = x_shape[x_str.find(indice)]
    elif indice in y_str:
      indice_dim = y_shape[y_str.find(indice)]
    else:
      raise ValueError('indice {} not found in inputs'.format(indice))
    shape_dic[indice] = indice_dim
    if indice not in r_str:
      contracted.add(indice)
  madds = np.prod([shape_dic[indice] for indice in r_str]) * (
      np.prod([shape_dic[indice] for indice in contracted]))
  flops = 2 * madds
  return ops.OpStats('flops', flops)