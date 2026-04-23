def get_vars_to_restore(ckpt=None):
  """Returns list of variables that should be saved/restored.

  Args:
    ckpt: Path to existing checkpoint.  If present, returns only the subset of
        variables that exist in given checkpoint.

  Returns:
    List of all variables that need to be saved/restored.
  """
  model_vars = tf.trainable_variables()
  # Add batchnorm variables.
  bn_vars = [v for v in tf.global_variables()
             if 'moving_mean' in v.op.name or 'moving_variance' in v.op.name]
  model_vars.extend(bn_vars)
  model_vars = sorted(model_vars, key=lambda x: x.op.name)
  if ckpt is not None:
    ckpt_var_names = tf.contrib.framework.list_variables(ckpt)
    ckpt_var_names = [name for (name, unused_shape) in ckpt_var_names]
    for v in model_vars:
      if v.op.name not in ckpt_var_names:
        logging.warn('Missing var %s in checkpoint: %s', v.op.name,
                     os.path.basename(ckpt))
    model_vars = [v for v in model_vars if v.op.name in ckpt_var_names]
  return model_vars