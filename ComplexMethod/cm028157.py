def main(_):
  """Get this whole shindig off the ground."""
  d = build_hyperparameter_dict(FLAGS)
  hps = hps_dict_to_obj(d)    # hyper parameters
  kind = FLAGS.kind

  # Read the data, if necessary.
  train_set = valid_set = None
  if kind in ["train", "posterior_sample_and_average", "posterior_push_mean",
              "prior_sample", "write_model_params"]:
    datasets = load_datasets(hps.data_dir, hps.data_filename_stem)
  else:
    raise ValueError('Kind {} is not supported.'.format(kind))

  # infer the dataset names and dataset dimensions from the loaded files
  hps.kind = kind     # needs to be added here, cuz not saved as hyperparam
  hps.dataset_names = []
  hps.dataset_dims = {}
  for key in datasets:
    hps.dataset_names.append(key)
    hps.dataset_dims[key] = datasets[key]['data_dim']

  # also store down the dimensionality of the data
  # - just pull from one set, required to be same for all sets
  hps.num_steps = datasets.values()[0]['num_steps']
  hps.ndatasets = len(hps.dataset_names)

  if hps.num_steps_for_gen_ic > hps.num_steps:
    hps.num_steps_for_gen_ic = hps.num_steps

  # Build and run the model, for varying purposes.
  config = tf.ConfigProto(allow_soft_placement=True,
                          log_device_placement=False)
  if FLAGS.allow_gpu_growth:
    config.gpu_options.allow_growth = True
  sess = tf.Session(config=config)
  with sess.as_default():
    with tf.device(hps.device):
      if kind == "train":
        train(hps, datasets)
      elif kind == "posterior_sample_and_average":
        write_model_runs(hps, datasets, hps.output_filename_stem,
                         push_mean=False)
      elif kind == "posterior_push_mean":
        write_model_runs(hps, datasets, hps.output_filename_stem,
                         push_mean=True)
      elif kind == "prior_sample":
        write_model_samples(hps, datasets, hps.output_filename_stem)
      elif kind == "write_model_params":
        write_model_parameters(hps, hps.output_filename_stem, datasets)
      else:
        assert False, ("Kind %s is not implemented. " % kind)