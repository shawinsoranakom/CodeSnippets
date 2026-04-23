def _generator_network(self, samples, logQ, log_likelihood_func=None):
    '''Returns learning signal and function.

    This is the implementation for SBNs for the ELBO.

    Args:
      samples: dictionary of sampled latent variables
      logQ: list of log q(h_i) terms
      log_likelihood_func: function used to compute log probs for the latent
        variables

    Returns:
      learning_signal: the "reward" function
      function_term: part of the function that depends on the parameters
        and needs to have the gradient taken through
    '''
    reuse=None if not self.run_generator_network else True

    if self.hparams.task in ['sbn', 'omni']:
      if log_likelihood_func is None:
        log_likelihood_func = lambda sample, log_params: (
          U.binary_log_likelihood(sample['activation'], log_params))

      logPPrior = log_likelihood_func(
          samples[self.hparams.n_layer-1],
          tf.expand_dims(self.prior, 0))

      with slim.arg_scope([slim.fully_connected],
                          weights_initializer=slim.variance_scaling_initializer(),
                          variables_collections=[P_COLLECTION]):

        for i in reversed(xrange(self.hparams.n_layer)):
          if i == 0:
            n_output = self.hparams.n_input
          else:
            n_output = self.hparams.n_hidden
          input = 2.0*samples[i]['activation']-1.0

          h = self._create_transformation(input,
                                          n_output,
                                          reuse=reuse,
                                          scope_prefix='p_%d' % i)

          if i == 0:
            # Assume output is binary
            logP = U.binary_log_likelihood(self._x, h + self.train_bias)
          else:
            logPPrior += log_likelihood_func(samples[i-1], h)

      self.run_generator_network = True
      return logP + logPPrior - tf.add_n(logQ), logP + logPPrior
    elif self.hparams.task == 'sp':
      with slim.arg_scope([slim.fully_connected],
                          weights_initializer=slim.variance_scaling_initializer(),
                          variables_collections=[P_COLLECTION]):
        n_output = int(self.hparams.n_input/2)
        i = self.hparams.n_layer - 1  # use the last layer
        input = 2.0*samples[i]['activation']-1.0

        h = self._create_transformation(input,
                                        n_output,
                                        reuse=reuse,
                                        scope_prefix='p_%d' % i)

        # Predict on the lower half of the image
        logP = U.binary_log_likelihood(tf.split(self._x,
                                              num_or_size_splits=2,
                                              axis=1)[1],
                                     h + np.split(self.train_bias, 2, 0)[1])

      self.run_generator_network = True
      return logP, logP