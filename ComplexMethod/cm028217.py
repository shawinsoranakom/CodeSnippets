def main(unused_argv):
  assert FLAGS.checkpoint_dir, '`checkpoint_dir` is missing.'
  assert FLAGS.eval_dir, '`eval_dir` is missing.'
  tf.gfile.MakeDirs(FLAGS.eval_dir)
  if FLAGS.pipeline_config_path:
    configs = config_util.get_configs_from_pipeline_file(
        FLAGS.pipeline_config_path)
    tf.gfile.Copy(
        FLAGS.pipeline_config_path,
        os.path.join(FLAGS.eval_dir, 'pipeline.config'),
        overwrite=True)
  else:
    configs = config_util.get_configs_from_multiple_files(
        model_config_path=FLAGS.model_config_path,
        eval_config_path=FLAGS.eval_config_path,
        eval_input_config_path=FLAGS.input_config_path)
    for name, config in [('model.config', FLAGS.model_config_path),
                         ('eval.config', FLAGS.eval_config_path),
                         ('input.config', FLAGS.input_config_path)]:
      tf.gfile.Copy(config, os.path.join(FLAGS.eval_dir, name), overwrite=True)

  model_config = configs['model']
  eval_config = configs['eval_config']
  input_config = configs['eval_input_config']
  if FLAGS.eval_training_data:
    input_config = configs['train_input_config']

  model_fn = functools.partial(
      model_builder.build, model_config=model_config, is_training=False)

  def get_next(config):
    return dataset_builder.make_initializable_iterator(
        dataset_builder.build(config)).get_next()

  create_input_dict_fn = functools.partial(get_next, input_config)

  categories = label_map_util.create_categories_from_labelmap(
      input_config.label_map_path)

  if FLAGS.run_once:
    eval_config.max_evals = 1

  graph_rewriter_fn = None
  if 'graph_rewriter_config' in configs:
    graph_rewriter_fn = graph_rewriter_builder.build(
        configs['graph_rewriter_config'], is_training=False)

  evaluator.evaluate(
      create_input_dict_fn,
      model_fn,
      eval_config,
      categories,
      FLAGS.checkpoint_dir,
      FLAGS.eval_dir,
      graph_hook_fn=graph_rewriter_fn)