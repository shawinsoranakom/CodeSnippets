def convert(checkpoint_from_path,
            checkpoint_to_path,
            num_heads,
            name_replacements,
            permutations,
            exclude_patterns=None):
  """Migrates the names of variables within a checkpoint.

  Args:
    checkpoint_from_path: Path to source checkpoint to be read in.
    checkpoint_to_path: Path to checkpoint to be written out.
    num_heads: The number of heads of the model.
    name_replacements: A list of tuples of the form (match_str, replace_str)
      describing variable names to adjust.
    permutations: A list of tuples of the form (match_str, permutation)
      describing permutations to apply to given variables. Note that match_str
      should match the original variable name, not the replaced one.
    exclude_patterns: A list of string patterns to exclude variables from
      checkpoint conversion.

  Returns:
    A dictionary that maps the new variable names to the Variable objects.
    A dictionary that maps the old variable names to the new variable names.
  """
  with tf.Graph().as_default():
    tf.logging.info("Reading checkpoint_from_path %s", checkpoint_from_path)
    reader = tf.train.NewCheckpointReader(checkpoint_from_path)
    name_shape_map = reader.get_variable_to_shape_map()
    new_variable_map = {}
    conversion_map = {}
    for var_name in name_shape_map:
      if exclude_patterns and _has_exclude_patterns(var_name, exclude_patterns):
        continue
      # Get the original tensor data.
      tensor = reader.get_tensor(var_name)

      # Look up the new variable name, if any.
      new_var_name = _bert_name_replacement(var_name, name_replacements)

      # See if we need to reshape the underlying tensor.
      new_shape = None
      if num_heads > 0:
        new_shape = _get_new_shape(new_var_name, tensor.shape, num_heads)
      if new_shape:
        tf.logging.info("Veriable %s has a shape change from %s to %s",
                        var_name, tensor.shape, new_shape)
        tensor = np.reshape(tensor, new_shape)

      # See if we need to permute the underlying tensor.
      permutation = _get_permutation(var_name, permutations)
      if permutation:
        tensor = np.transpose(tensor, permutation)

      # Create a new variable with the possibly-reshaped or transposed tensor.
      var = tf.Variable(tensor, name=var_name)

      # Save the variable into the new variable map.
      new_variable_map[new_var_name] = var

      # Keep a list of converter variables for sanity checking.
      if new_var_name != var_name:
        conversion_map[var_name] = new_var_name

    saver = tf.train.Saver(new_variable_map)

    with tf.Session() as sess:
      sess.run(tf.global_variables_initializer())
      tf.logging.info("Writing checkpoint_to_path %s", checkpoint_to_path)
      saver.save(sess, checkpoint_to_path, write_meta_graph=False)

  tf.logging.info("Summary:")
  tf.logging.info("  Converted %d variable name(s).", len(new_variable_map))
  tf.logging.info("  Converted: %s", str(conversion_map))