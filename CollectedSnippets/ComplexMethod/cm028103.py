def train(sbn, train_xs, valid_xs, test_xs, training_steps, debug=False):
  hparams = sorted(sbn.hparams.values().items())
  hparams = (map(str, x) for x in hparams)
  hparams = ('_'.join(x) for x in hparams)
  hparams_str = '.'.join(hparams)

  logger = L.Logger()

  # Create the experiment name from the hparams
  experiment_name = ([str(sbn.hparams.n_hidden) for i in xrange(sbn.hparams.n_layer)] +
                     [str(sbn.hparams.n_input)])
  if sbn.hparams.nonlinear:
    experiment_name = '~'.join(experiment_name)
  else:
    experiment_name = '-'.join(experiment_name)
  experiment_name = 'SBN_%s' % experiment_name
  rowkey = {'experiment': experiment_name,
            'model': hparams_str}

  # Create summary writer
  summ_dir = os.path.join(FLAGS.working_dir, hparams_str)
  summary_writer = tf.summary.FileWriter(
      summ_dir, flush_secs=15, max_queue=100)

  sv = tf.train.Supervisor(logdir=os.path.join(
      FLAGS.working_dir, hparams_str),
                     save_summaries_secs=0,
                     save_model_secs=1200,
                     summary_op=None,
                     recovery_wait_secs=30,
                     global_step=sbn.global_step)
  with sv.managed_session() as sess:
    # Dump hparams to file
    with gfile.Open(os.path.join(FLAGS.working_dir,
                                 hparams_str,
                                 'hparams.json'),
                    'w') as out:
      json.dump(sbn.hparams.values(), out)

    sbn.initialize(sess)
    batch_size = sbn.hparams.batch_size
    scores = []
    n = train_xs.shape[0]
    index = range(n)

    while not sv.should_stop():
      lHats = []
      grad_variances = []
      temperatures = []
      random.shuffle(index)
      i = 0
      while i < n:
        batch_index = index[i:min(i+batch_size, n)]
        batch_xs = train_xs[batch_index, :]

        if sbn.hparams.dynamic_b:
          # Dynamically binarize the batch data
          batch_xs = (np.random.rand(*batch_xs.shape) < batch_xs).astype(float)

        lHat, grad_variance, step, temperature = sbn.partial_fit(batch_xs,
                                                    sbn.hparams.n_samples)
        if debug:
          print(i, lHat)
          if i > 100:
            return
        lHats.append(lHat)
        grad_variances.append(grad_variance)
        temperatures.append(temperature)
        i += batch_size

      grad_variances = np.log(np.mean(grad_variances, axis=0)).tolist()
      summary_strings = []
      if isinstance(grad_variances, list):
        grad_variances = dict(zip([k for (k, v) in sbn.losses], map(float, grad_variances)))
        rowkey['step'] = step
        logger.log(rowkey, {'step': step,
                             'train': np.mean(lHats, axis=0)[0],
                             'grad_variances': grad_variances,
                             'temperature': np.mean(temperatures), })
        grad_variances = '\n'.join(map(str, sorted(grad_variances.iteritems())))
      else:
        rowkey['step'] = step
        logger.log(rowkey, {'step': step,
                             'train': np.mean(lHats, axis=0)[0],
                             'grad_variance': grad_variances,
                             'temperature': np.mean(temperatures), })
        summary_strings.append(manual_scalar_summary("log grad variance", grad_variances))

      print('Step %d: %s\n%s' % (step, str(np.mean(lHats, axis=0)), str(grad_variances)))

      # Every few epochs compute test and validation scores
      epoch = int(step / (train_xs.shape[0] / sbn.hparams.batch_size))
      if epoch % FLAGS.eval_freq == 0:
        valid_res = eval(sbn, valid_xs)
        test_res= eval(sbn, test_xs)

        print('\nValid %d: %s' % (step, str(valid_res)))
        print('Test %d: %s\n' % (step, str(test_res)))
        logger.log(rowkey, {'step': step,
                             'valid': valid_res[0],
                             'test': test_res[0]})
        logger.flush()  # Flush infrequently

      # Create summaries
      summary_strings.extend([
        manual_scalar_summary("Train ELBO", np.mean(lHats, axis=0)[0]),
        manual_scalar_summary("Temperature", np.mean(temperatures)),
      ])
      for summ_str in summary_strings:
        summary_writer.add_summary(summ_str, global_step=step)
      summary_writer.flush()

      sys.stdout.flush()
      scores.append(np.mean(lHats, axis=0))

      if step > training_steps:
        break

    return scores