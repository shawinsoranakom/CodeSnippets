def eval_model_runs_avg_epoch(self, data_name, data_extxd,
                                ext_input_extxi=None):
    """Returns all the expected value for goodies for the entire model.

    The expected value is taken over hidden (z) variables, namely the initial
    conditions and the control inputs.  The expected value is approximate, and
    accomplished via sampling (batch_size) samples for every examples.

    Args:
      data_name: The name of the data dict, to select which in/out matrices
        to use.
      data_extxd: Numpy array training data with shape:
        # examples x # time steps x # dimensions
      ext_input_extxi (optional): Numpy array training external input with
        shape: # examples x # time steps x # external input dims

    Returns:
      A dictionary with the averaged outputs of the model decoder, namely:
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
    for es_idx in range(E_to_process):
      print("Running %d of %d." % (es_idx+1, E_to_process))
      example_idxs = es_idx * np.ones(batch_size, dtype=np.int32)
      data_bxtxd, ext_input_bxtxi = self.get_batch(data_extxd,
                                                   ext_input_extxi,
                                                   batch_size=batch_size,
                                                   example_idxs=example_idxs)
      model_values = self.eval_model_runs_batch(data_name, data_bxtxd,
                                                ext_input_bxtxi,
                                                do_eval_cost=True,
                                                do_average_batch=True)

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
      costs[es_idx] = model_values['costs']
      nll_bound_vaes[es_idx] = model_values['nll_bound_vaes']
      nll_bound_iwaes[es_idx] = model_values['nll_bound_iwaes']
      train_steps[es_idx] = model_values['train_steps']
      print('bound nll(vae): %.3f, bound nll(iwae): %.3f' \
            % (nll_bound_vaes[es_idx], nll_bound_iwaes[es_idx]))

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
    model_runs['costs'] = costs
    model_runs['nll_bound_vaes'] = nll_bound_vaes
    model_runs['nll_bound_iwaes'] = nll_bound_iwaes
    model_runs['train_steps'] = train_steps
    return model_runs