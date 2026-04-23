def write_model_samples(self, dataset_name, output_fname=None):
    """Use the prior distribution to generate batch_size number of samples
    from the model.

    LFADS generates a number of outputs for each sample, and these are all
    saved.  They are:
      The mean and variance of the prior of g0.
      The control inputs (if enabled).
      The initial conditions, g0, for all examples.
      The generator states for all time.
      The factors for all time.
      The output distribution parameters (e.g. rates) for all time.

    Args:
      dataset_name: The name of the dataset to grab the factors -> rates
      alignment matrices from.
      output_fname: The name of the file in which to save the generated
        samples.
    """
    hps = self.hps
    batch_size = hps.batch_size

    print("Generating %d samples" % (batch_size))
    tf_vals = [self.factors, self.gen_states, self.gen_ics,
               self.cost, self.output_dist_params]
    if hps.ic_dim > 0:
      tf_vals += [self.prior_zs_g0.mean, self.prior_zs_g0.logvar]
    if hps.co_dim > 0:
      tf_vals += [self.prior_zs_ar_con.samples_t]
    tf_vals_flat, fidxs = flatten(tf_vals)

    session = tf.get_default_session()
    feed_dict = {}
    feed_dict[self.dataName] = dataset_name
    feed_dict[self.keep_prob] = 1.0

    np_vals_flat = session.run(tf_vals_flat, feed_dict=feed_dict)

    ff = 0
    factors = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    gen_states = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    gen_ics = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    costs = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    output_dist_params = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    if hps.ic_dim > 0:
      prior_g0_mean = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
      prior_g0_logvar = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1
    if hps.co_dim > 0:
      prior_zs_ar_con = [np_vals_flat[f] for f in fidxs[ff]]; ff += 1

    # [0] are to take out the non-temporal items from lists
    gen_ics = gen_ics[0]
    costs = costs[0]

    # Convert to full tensors, not lists of tensors in time dim.
    gen_states = list_t_bxn_to_tensor_bxtxn(gen_states)
    factors = list_t_bxn_to_tensor_bxtxn(factors)
    output_dist_params = list_t_bxn_to_tensor_bxtxn(output_dist_params)
    if hps.ic_dim > 0:
      prior_g0_mean = prior_g0_mean[0]
      prior_g0_logvar = prior_g0_logvar[0]
    if hps.co_dim > 0:
      prior_zs_ar_con = list_t_bxn_to_tensor_bxtxn(prior_zs_ar_con)

    model_vals = {}
    model_vals['gen_ics'] = gen_ics
    model_vals['gen_states'] = gen_states
    model_vals['factors'] = factors
    model_vals['output_dist_params'] = output_dist_params
    model_vals['costs'] = costs.reshape(1)
    if hps.ic_dim > 0:
      model_vals['prior_g0_mean'] = prior_g0_mean
      model_vals['prior_g0_logvar'] = prior_g0_logvar
    if hps.co_dim > 0:
      model_vals['prior_zs_ar_con'] = prior_zs_ar_con

    full_fname = os.path.join(hps.lfads_save_dir, output_fname)
    write_data(full_fname, model_vals, compression='gzip')
    print("Done.")