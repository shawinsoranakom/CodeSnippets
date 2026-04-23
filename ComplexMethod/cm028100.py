def _recognition_network(self, sampler=None, log_likelihood_func=None):
    """x values -> samples from Q and return log Q(h|x)."""
    samples = {}
    reuse = None if not self.run_recognition_network else True

    # Set defaults
    if sampler is None:
      sampler = self._random_sample

    if log_likelihood_func is None:
      log_likelihood_func = lambda sample, log_params: (
        U.binary_log_likelihood(sample['activation'], log_params))

    logQ = []


    if self.hparams.task in ['sbn', 'omni']:
      # Initialize the edge case
      samples[-1] = {'activation': self._x}
      if self.mean_xs is not None:
        samples[-1]['activation'] -= self.mean_xs  # center the input
      samples[-1]['activation'] = (samples[-1]['activation'] + 1)/2.0

      with slim.arg_scope([slim.fully_connected],
                          weights_initializer=slim.variance_scaling_initializer(),
                          variables_collections=[Q_COLLECTION]):
        for i in xrange(self.hparams.n_layer):
          # Set up the input to the layer
          input = 2.0*samples[i-1]['activation'] - 1.0

          # Create the conditional distribution (output is the logits)
          h = self._create_transformation(input,
                                          n_output=self.hparams.n_hidden,
                                          reuse=reuse,
                                          scope_prefix='q_%d' % i)

          samples[i] = sampler(h, self.uniform_samples[i], i)
          logQ.append(log_likelihood_func(samples[i], h))

      self.run_recognition_network = True
      return logQ, samples
    elif self.hparams.task == 'sp':
      # Initialize the edge case
      samples[-1] = {'activation': tf.split(self._x,
                                            num_or_size_splits=2,
                                            axis=1)[0]}  # top half of digit
      if self.mean_xs is not None:
        samples[-1]['activation'] -= np.split(self.mean_xs, 2, 0)[0]  # center the input
      samples[-1]['activation'] = (samples[-1]['activation'] + 1)/2.0

      with slim.arg_scope([slim.fully_connected],
                          weights_initializer=slim.variance_scaling_initializer(),
                          variables_collections=[Q_COLLECTION]):
        for i in xrange(self.hparams.n_layer):
          # Set up the input to the layer
          input = 2.0*samples[i-1]['activation'] - 1.0

          # Create the conditional distribution (output is the logits)
          h = self._create_transformation(input,
                                          n_output=self.hparams.n_hidden,
                                          reuse=reuse,
                                          scope_prefix='q_%d' % i)

          samples[i] = sampler(h, self.uniform_samples[i], i)
          logQ.append(log_likelihood_func(samples[i], h))

      self.run_recognition_network = True
      return logQ, samples