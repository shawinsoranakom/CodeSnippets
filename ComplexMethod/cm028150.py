def eval_model_runs_batch(self, data_name, data_bxtxd, ext_input_bxtxi=None,
                            do_eval_cost=False, do_average_batch=False):
    """Returns all the goodies for the entire model, per batch.

    If data_bxtxd and ext_input_bxtxi can have fewer than batch_size along dim 1
    in which case this handles the padding and truncating automatically

    Args:
      data_name: The name of the data dict, to select which in/out matrices
        to use.
      data_bxtxd: Numpy array training data with shape:
        batch_size x # time steps x # dimensions
      ext_input_bxtxi: Numpy array training external input with shape:
        batch_size x # time steps x # external input dims
      do_eval_cost (optional): If true, the IWAE (Importance Weighted
        Autoencoder) log likeihood bound, instead of the VAE version.
      do_average_batch (optional): average over the batch, useful for getting
      good IWAE costs, and model outputs for a single data point.

    Returns:
      A dictionary with the outputs of the model decoder, namely:
        prior g0 mean, prior g0 variance, approx. posterior mean, approx
        posterior mean, the generator initial conditions, the control inputs (if
        enabled), the state of the generator, the factors, and the rates.
    """
    session = tf.get_default_session()

    # if fewer than batch_size provided, pad to batch_size
    hps = self.hps
    batch_size = hps.batch_size
    E, _, _ = data_bxtxd.shape
    if E < hps.batch_size:
      data_bxtxd = np.pad(data_bxtxd, ((0, hps.batch_size-E), (0, 0), (0, 0)),
                          mode='constant', constant_values=0)
      if ext_input_bxtxi is not None:
        ext_input_bxtxi = np.pad(ext_input_bxtxi,
                                 ((0, hps.batch_size-E), (0, 0), (0, 0)),
                                 mode='constant', constant_values=0)

    feed_dict = self.build_feed_dict(data_name, data_bxtxd,
                                     ext_input_bxtxi, keep_prob=1.0)

    # Non-temporal signals will be batch x dim.
    # Temporal signals are list length T with elements batch x dim.
    tf_vals = [self.gen_ics, self.gen_states, self.factors,
               self.output_dist_params]
    tf_vals.append(self.cost)
    tf_vals.append(self.nll_bound_vae)
    tf_vals.append(self.nll_bound_iwae)
    tf_vals.append(self.train_step) # not train_op!
    if self.hps.ic_dim > 0:
      tf_vals += [self.prior_zs_g0.mean, self.prior_zs_g0.logvar,
                  self.posterior_zs_g0.mean, self.posterior_zs_g0.logvar]
    if self.hps.co_dim > 0:
      tf_vals.append(self.controller_outputs)
    tf_vals_flat, fidxs = flatten(tf_vals)

    np_vals_flat = session.run(tf_vals_flat, feed_dict=feed_dict)

    ff = 0
    gen_ics = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    gen_states = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    factors = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    out_dist_params = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    costs = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    nll_bound_vaes = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    nll_bound_iwaes = [np_vals_flat[f] for f in fidxs[ff]]; ff +=1
    train_steps = [np_vals_flat[f] for f in fidxs[ff]]; ff +=1
    if self.hps.ic_dim > 0:
      prior_g0_mean = [np_vals_flat[f] for f in fidxs[ff]]; ff +=1
      prior_g0_logvar = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
      post_g0_mean = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
      post_g0_logvar = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    if self.hps.co_dim > 0:
      controller_outputs = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1

    # [0] are to take out the non-temporal items from lists
    gen_ics = gen_ics[0]
    costs = costs[0]
    nll_bound_vaes = nll_bound_vaes[0]
    nll_bound_iwaes = nll_bound_iwaes[0]
    train_steps = train_steps[0]

    # Convert to full tensors, not lists of tensors in time dim.
    gen_states = list_t_bxn_to_tensor_bxtxn(gen_states)
    factors = list_t_bxn_to_tensor_bxtxn(factors)
    out_dist_params = list_t_bxn_to_tensor_bxtxn(out_dist_params)
    if self.hps.ic_dim > 0:
      # select first time point
      prior_g0_mean = prior_g0_mean[0]
      prior_g0_logvar = prior_g0_logvar[0]
      post_g0_mean = post_g0_mean[0]
      post_g0_logvar = post_g0_logvar[0]
    if self.hps.co_dim > 0:
      controller_outputs = list_t_bxn_to_tensor_bxtxn(controller_outputs)

    # slice out the trials in case < batch_size provided
    if E < hps.batch_size:
      idx = np.arange(E)
      gen_ics = gen_ics[idx, :]
      gen_states = gen_states[idx, :]
      factors = factors[idx, :, :]
      out_dist_params = out_dist_params[idx, :, :]
      if self.hps.ic_dim > 0:
        prior_g0_mean = prior_g0_mean[idx, :]
        prior_g0_logvar = prior_g0_logvar[idx, :]
        post_g0_mean = post_g0_mean[idx, :]
        post_g0_logvar = post_g0_logvar[idx, :]
      if self.hps.co_dim > 0:
        controller_outputs = controller_outputs[idx, :, :]

    if do_average_batch:
      gen_ics = np.mean(gen_ics, axis=0)
      gen_states = np.mean(gen_states, axis=0)
      factors = np.mean(factors, axis=0)
      out_dist_params = np.mean(out_dist_params, axis=0)
      if self.hps.ic_dim > 0:
        prior_g0_mean = np.mean(prior_g0_mean, axis=0)
        prior_g0_logvar = np.mean(prior_g0_logvar, axis=0)
        post_g0_mean = np.mean(post_g0_mean, axis=0)
        post_g0_logvar = np.mean(post_g0_logvar, axis=0)
      if self.hps.co_dim > 0:
        controller_outputs = np.mean(controller_outputs, axis=0)

    model_vals = {}
    model_vals['gen_ics'] = gen_ics
    model_vals['gen_states'] = gen_states
    model_vals['factors'] = factors
    model_vals['output_dist_params'] = out_dist_params
    model_vals['costs'] = costs
    model_vals['nll_bound_vaes'] = nll_bound_vaes
    model_vals['nll_bound_iwaes'] = nll_bound_iwaes
    model_vals['train_steps'] = train_steps
    if self.hps.ic_dim > 0:
      model_vals['prior_g0_mean'] = prior_g0_mean
      model_vals['prior_g0_logvar'] = prior_g0_logvar
      model_vals['post_g0_mean'] = post_g0_mean
      model_vals['post_g0_logvar'] = post_g0_logvar
    if self.hps.co_dim > 0:
      model_vals['controller_outputs'] = controller_outputs

    return model_vals