def eval_model_runs_push_mean(self, data_name, data_extxd,
                                ext_input_extxi=None):
    """Returns values of interest for the model by pushing the means through

    The mean values for both initial conditions and the control inputs are
    pushed through the model instead of sampling (as is done in
    eval_model_runs_avg_epoch).
    This is a quick and approximate version of estimating these values instead
    of sampling from the posterior many times and then averaging those values of
    interest.

    Internally, a total of batch_size trials are run through the model at once.

    Args:
      data_name: The name of the data dict, to select which in/out matrices
        to use.
      data_extxd: Numpy array training data with shape:
        # examples x # time steps x # dimensions
      ext_input_extxi (optional): Numpy array training external input with
        shape: # examples x # time steps x # external input dims

    Returns:
      A dictionary with the estimated outputs of the model decoder, namely:
        prior g0 mean, prior g0 variance, approx. posterior mean, approx
        posterior mean, the generator initial conditions, the control inputs (if
        enabled), the state of the generator, the factors, and the output
        distribution parameters, e.g. (rates or mean and variances).
    """
    hps = self.hps
    batch_size = hps.batch_size
    E, T, D  = data_extxd.shape
    E_to_process = hps.ps_nexamples_to_process
    if E_to_process > E:
      print("Setting number of posterior samples to process to : ", E)
      E_to_process = E

    if hps.ic_dim > 0:
      prior_g0_mean = np.zeros([E_to_process, hps.ic_dim])
      prior_g0_logvar = np.zeros([E_to_process, hps.ic_dim])
      post_g0_mean = np.zeros([E_to_process, hps.ic_dim])
      post_g0_logvar = np.zeros([E_to_process, hps.ic_dim])

    if hps.co_dim > 0:
      controller_outputs = np.zeros([E_to_process, T, hps.co_dim])
    gen_ics = np.zeros([E_to_process, hps.gen_dim])
    gen_states = np.zeros([E_to_process, T, hps.gen_dim])
    factors = np.zeros([E_to_process, T, hps.factors_dim])

    if hps.output_dist == 'poisson':
      out_dist_params = np.zeros([E_to_process, T, D])
    elif hps.output_dist == 'gaussian':
      out_dist_params = np.zeros([E_to_process, T, D+D])
    else:
      assert False, "NIY"

    costs = np.zeros(E_to_process)
    nll_bound_vaes = np.zeros(E_to_process)
    nll_bound_iwaes = np.zeros(E_to_process)
    train_steps = np.zeros(E_to_process)

    # generator that will yield 0:N in groups of per items, e.g.
    # (0:per-1), (per:2*per-1), ..., with the last group containing <= per items
    # this will be used to feed per=batch_size trials into the model at a time
    def trial_batches(N, per):
      for i in range(0, N, per):
        yield np.arange(i, min(i+per, N), dtype=np.int32)

    for batch_idx, es_idx in enumerate(trial_batches(E_to_process,
                                                     hps.batch_size)):
      print("Running trial batch %d with %d trials" % (batch_idx+1,
                                                       len(es_idx)))
      data_bxtxd, ext_input_bxtxi = self.get_batch(data_extxd,
                                                   ext_input_extxi,
                                                   batch_size=batch_size,
                                                   example_idxs=es_idx)
      model_values = self.eval_model_runs_batch(data_name, data_bxtxd,
                                                ext_input_bxtxi,
                                                do_eval_cost=True,
                                                do_average_batch=False)

      if self.hps.ic_dim > 0:
        prior_g0_mean[es_idx,:] = model_values['prior_g0_mean']
        prior_g0_logvar[es_idx,:] = model_values['prior_g0_logvar']
        post_g0_mean[es_idx,:] = model_values['post_g0_mean']
        post_g0_logvar[es_idx,:] = model_values['post_g0_logvar']
      gen_ics[es_idx,:] = model_values['gen_ics']

      if self.hps.co_dim > 0:
        controller_outputs[es_idx,:,:] = model_values['controller_outputs']
      gen_states[es_idx,:,:] = model_values['gen_states']
      factors[es_idx,:,:] = model_values['factors']
      out_dist_params[es_idx,:,:] = model_values['output_dist_params']

      # TODO
      # model_values['costs'] and other costs come out as scalars, summed over
      # all the trials in the batch. what we want is the per-trial costs
      costs[es_idx] = model_values['costs']
      nll_bound_vaes[es_idx] = model_values['nll_bound_vaes']
      nll_bound_iwaes[es_idx] = model_values['nll_bound_iwaes']

      train_steps[es_idx] = model_values['train_steps']

    model_runs = {}
    if self.hps.ic_dim > 0:
      model_runs['prior_g0_mean'] = prior_g0_mean
      model_runs['prior_g0_logvar'] = prior_g0_logvar
      model_runs['post_g0_mean'] = post_g0_mean
      model_runs['post_g0_logvar'] = post_g0_logvar
    model_runs['gen_ics'] = gen_ics

    if self.hps.co_dim > 0:
      model_runs['controller_outputs'] = controller_outputs
    model_runs['gen_states'] = gen_states
    model_runs['factors'] = factors
    model_runs['output_dist_params'] = out_dist_params

    # You probably do not want the LL associated values when pushing the mean
    # instead of sampling.
    model_runs['costs'] = costs
    model_runs['nll_bound_vaes'] = nll_bound_vaes
    model_runs['nll_bound_iwaes'] = nll_bound_iwaes
    model_runs['train_steps'] = train_steps
    return model_runs