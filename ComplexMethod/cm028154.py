def eval_model_parameters(use_nested=True, include_strs=None):
    """Evaluate and return all of the TF variables in the model.

    Args:
    use_nested (optional): For returning values, use a nested dictoinary, based
      on variable scoping, or return all variables in a flat dictionary.
    include_strs (optional): A list of strings to use as a filter, to reduce the
      number of variables returned.  A variable name must contain at least one
      string in include_strs as a sub-string in order to be returned.

    Returns:
      The parameters of the model.  This can be in a flat
      dictionary, or a nested dictionary, where the nesting is by variable
      scope.
    """
    all_tf_vars = tf.global_variables()
    session = tf.get_default_session()
    all_tf_vars_eval = session.run(all_tf_vars)
    vars_dict = {}
    strs = ["LFADS"]
    if include_strs:
      strs += include_strs

    for i, (var, var_eval) in enumerate(zip(all_tf_vars, all_tf_vars_eval)):
      if any(s in include_strs for s in var.name):
        if not isinstance(var_eval, np.ndarray): # for H5PY
          print(var.name, """ is not numpy array, saving as numpy array
                with value: """, var_eval, type(var_eval))
          e = np.array(var_eval)
          print(e, type(e))
        else:
          e = var_eval
        vars_dict[var.name] = e

    if not use_nested:
      return vars_dict

    var_names = vars_dict.keys()
    nested_vars_dict = {}
    current_dict = nested_vars_dict
    for v, var_name in enumerate(var_names):
      var_split_name_list = var_name.split('/')
      split_name_list_len = len(var_split_name_list)
      current_dict = nested_vars_dict
      for p, part in enumerate(var_split_name_list):
        if p < split_name_list_len - 1:
          if part in current_dict:
            current_dict = current_dict[part]
          else:
            current_dict[part] = {}
            current_dict = current_dict[part]
        else:
          current_dict[part] = vars_dict[var_name]

    return nested_vars_dict