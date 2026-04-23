def build_model(hps, kind="train", datasets=None):
  """Builds a model from either random initialization, or saved parameters.

  Args:
    hps: The hyper parameters for the model.
    kind: (optional) The kind of model to build.  Training vs inference require
      different graphs.
    datasets: The datasets structure (see top of lfads.py).

  Returns:
    an LFADS model.
  """

  build_kind = kind
  if build_kind == "write_model_params":
    build_kind = "train"
  with tf.variable_scope("LFADS", reuse=None):
    model = LFADS(hps, kind=build_kind, datasets=datasets)

  if not os.path.exists(hps.lfads_save_dir):
    print("Save directory %s does not exist, creating it." % hps.lfads_save_dir)
    os.makedirs(hps.lfads_save_dir)

  cp_pb_ln = hps.checkpoint_pb_load_name
  cp_pb_ln = 'checkpoint' if cp_pb_ln == "" else cp_pb_ln
  if cp_pb_ln == 'checkpoint':
    print("Loading latest training checkpoint in: ", hps.lfads_save_dir)
    saver = model.seso_saver
  elif cp_pb_ln == 'checkpoint_lve':
    print("Loading lowest validation checkpoint in: ", hps.lfads_save_dir)
    saver = model.lve_saver
  else:
    print("Loading checkpoint: ", cp_pb_ln, ", in: ", hps.lfads_save_dir)
    saver = model.seso_saver

  ckpt = tf.train.get_checkpoint_state(hps.lfads_save_dir,
                                       latest_filename=cp_pb_ln)

  session = tf.get_default_session()
  print("ckpt: ", ckpt)
  if ckpt and tf.train.checkpoint_exists(ckpt.model_checkpoint_path):
    print("Reading model parameters from %s" % ckpt.model_checkpoint_path)
    saver.restore(session, ckpt.model_checkpoint_path)
  else:
    print("Created model with fresh parameters.")
    if kind in ["posterior_sample_and_average", "posterior_push_mean",
                "prior_sample", "write_model_params"]:
      print("Possible error!!! You are running ", kind, " on a newly \
      initialized model!")
      # cannot print ckpt.model_check_point path if no ckpt
      print("Are you sure you sure a checkpoint in ", hps.lfads_save_dir,
            " exists?")

    tf.global_variables_initializer().run()

  if ckpt:
    train_step_str = re.search('-[0-9]+$', ckpt.model_checkpoint_path).group()
  else:
    train_step_str = '-0'

  fname = 'hyperparameters' + train_step_str + '.txt'
  hp_fname = os.path.join(hps.lfads_save_dir, fname)
  hps_for_saving = jsonify_dict(hps)
  utils.write_data(hp_fname, hps_for_saving, use_json=True)

  return model