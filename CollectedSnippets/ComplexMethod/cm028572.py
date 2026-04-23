def main(_):

  params = exp_factory.get_exp_config(FLAGS.experiment)
  for config_file in FLAGS.config_file or []:
    params = hyperparams.override_params_dict(
        params, config_file, is_strict=False)
  if FLAGS.params_override:
    params = hyperparams.override_params_dict(
        params, FLAGS.params_override, is_strict=False)

  params.validate()
  params.lock()

  input_image_size = [int(x) for x in FLAGS.input_image_size.split(',')]
  input_specs = tf_keras.layers.InputSpec(
      shape=[FLAGS.batch_size] + input_image_size + [3])
  if FLAGS.experiment == 'maskconver_coco':
    model = factory.build_maskconver_model(
        input_specs=input_specs,
        model_config=params.task.model,
        l2_regularizer=None)
  elif FLAGS.experiment == 'multiscale_maskconver_coco':
    model = factory.build_multiscale_maskconver_model(
        input_specs=input_specs,
        model_config=params.task.model,
        l2_regularizer=None)

  export_module = maskconver.MaskConverModule(
      params=params,
      model=model,
      batch_size=FLAGS.batch_size,
      input_image_size=[int(x) for x in FLAGS.input_image_size.split(',')],
      input_type=FLAGS.input_type,
      num_channels=3)
  export_saved_model_lib.export_inference_graph(
      input_type=FLAGS.input_type,
      batch_size=FLAGS.batch_size,
      input_image_size=input_image_size,
      params=params,
      checkpoint_path=FLAGS.checkpoint_path,
      export_dir=FLAGS.export_dir,
      export_module=export_module,
      export_checkpoint_subdir='checkpoint',
      export_saved_model_subdir='saved_model')