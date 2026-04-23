def export(export_module: ExportModule,
           function_keys: Union[List[Text], Dict[Text, Text]],
           export_savedmodel_dir: Text,
           checkpoint_path: Optional[Text] = None,
           timestamped: bool = True,
           save_options: Optional[tf.saved_model.SaveOptions] = None,
           checkpoint: Optional[tf.train.Checkpoint] = None) -> Text:
  """Exports to SavedModel format.

  Args:
    export_module: a ExportModule with the keras Model and serving tf.functions.
    function_keys: a list of string keys to retrieve pre-defined serving
      signatures. The signaute keys will be set with defaults. If a dictionary
      is provided, the values will be used as signature keys.
    export_savedmodel_dir: Output saved model directory.
    checkpoint_path: Object-based checkpoint path or directory.
    timestamped: Whether to export the savedmodel to a timestamped directory.
    save_options: `SaveOptions` for `tf.saved_model.save`.
    checkpoint: An optional tf.train.Checkpoint. If provided, the export module
      will use it to read the weights.

  Returns:
    The savedmodel directory path.
  """
  ckpt_dir_or_file = checkpoint_path
  if ckpt_dir_or_file is not None and tf.io.gfile.isdir(ckpt_dir_or_file):
    ckpt_dir_or_file = tf.train.latest_checkpoint(ckpt_dir_or_file)
  if ckpt_dir_or_file:
    if checkpoint is None:
      checkpoint = tf.train.Checkpoint(model=export_module.model)
    checkpoint.read(
        ckpt_dir_or_file).assert_existing_objects_matched().expect_partial()
  if isinstance(function_keys, list):
    if len(function_keys) == 1:
      function_keys = {
          function_keys[0]: tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY
      }
    else:
      raise ValueError(
          'If the function_keys is a list, it must contain a single element. %s'
          % function_keys)

  signatures = export_module.get_inference_signatures(function_keys)
  if timestamped:
    export_dir = get_timestamped_export_dir(export_savedmodel_dir).decode(
        'utf-8')
  else:
    export_dir = export_savedmodel_dir
  tf.saved_model.save(
      export_module, export_dir, signatures=signatures, options=save_options)
  return export_dir