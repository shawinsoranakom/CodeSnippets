def __init__(self, hps, kind="train", datasets=None):
    """Create an LFADS model.

       train - a model for training, sampling of posteriors is used
       posterior_sample_and_average - sample from the posterior, this is used
         for evaluating the expected value of the outputs of LFADS, given a
         specific input, by averaging over multiple samples from the approx
         posterior.  Also used for the lower bound on the negative
         log-likelihood using IWAE error (Importance Weighed Auto-encoder).
         This is the denoising operation.
       prior_sample - a model for generation - sampling from priors is used

    Args:
      hps: The dictionary of hyper parameters.
      kind: The type of model to build (see above).
      datasets: A dictionary of named data_dictionaries, see top of lfads.py
    """
    print("Building graph...")
    all_kinds = ['train', 'posterior_sample_and_average', 'posterior_push_mean',
                 'prior_sample']
    assert kind in all_kinds, 'Wrong kind'
    if hps.feedback_factors_or_rates == "rates":
      assert len(hps.dataset_names) == 1, \
      "Multiple datasets not supported for rate feedback."
    num_steps = hps.num_steps
    ic_dim = hps.ic_dim
    co_dim = hps.co_dim
    ext_input_dim = hps.ext_input_dim
    cell_class = GRU
    gen_cell_class = GenGRU

    def makelambda(v):          # Used with tf.case
      return lambda: v

    # Define the data placeholder, and deal with all parts of the graph
    # that are dataset dependent.
    self.dataName = tf.placeholder(tf.string, shape=())
    # The batch_size to be inferred from data, as normal.
    # Additionally, the data_dim will be inferred as well, allowing for a
    # single placeholder for all datasets, regardless of data dimension.
    if hps.output_dist == 'poisson':
      # Enforce correct dtype
      assert np.issubdtype(
          datasets[hps.dataset_names[0]]['train_data'].dtype, int), \
          "Data dtype must be int for poisson output distribution"
      data_dtype = tf.int32
    elif hps.output_dist == 'gaussian':
      assert np.issubdtype(
          datasets[hps.dataset_names[0]]['train_data'].dtype, float), \
          "Data dtype must be float for gaussian output dsitribution"
      data_dtype = tf.float32
    else:
      assert False, "NIY"
    self.dataset_ph = dataset_ph = tf.placeholder(data_dtype,
                                                  [None, num_steps, None],
                                                  name="data")
    self.train_step = tf.get_variable("global_step", [], tf.int64,
                                      tf.zeros_initializer(),
                                      trainable=False)
    self.hps = hps
    ndatasets = hps.ndatasets
    factors_dim = hps.factors_dim
    self.preds = preds = [None] * ndatasets
    self.fns_in_fac_Ws = fns_in_fac_Ws = [None] * ndatasets
    self.fns_in_fatcor_bs = fns_in_fac_bs = [None] * ndatasets
    self.fns_out_fac_Ws = fns_out_fac_Ws = [None] * ndatasets
    self.fns_out_fac_bs = fns_out_fac_bs = [None] * ndatasets
    self.datasetNames = dataset_names = hps.dataset_names
    self.ext_inputs = ext_inputs = None

    if len(dataset_names) == 1:  # single session
      if 'alignment_matrix_cxf' in datasets[dataset_names[0]].keys():
        used_in_factors_dim = factors_dim
        in_identity_if_poss = False
      else:
        used_in_factors_dim = hps.dataset_dims[dataset_names[0]]
        in_identity_if_poss = True
    else:  # multisession
      used_in_factors_dim = factors_dim
      in_identity_if_poss = False

    for d, name in enumerate(dataset_names):
      data_dim = hps.dataset_dims[name]
      in_mat_cxf = None
      in_bias_1xf = None
      align_bias_1xc = None

      if datasets and 'alignment_matrix_cxf' in datasets[name].keys():
        dataset = datasets[name]
        if hps.do_train_readin:
            print("Initializing trainable readin matrix with alignment matrix" \
                  " provided for dataset:", name)
        else:
            print("Setting non-trainable readin matrix to alignment matrix" \
                  " provided for dataset:", name)
        in_mat_cxf = dataset['alignment_matrix_cxf'].astype(np.float32)
        if in_mat_cxf.shape != (data_dim, factors_dim):
          raise ValueError("""Alignment matrix must have dimensions %d x %d
          (data_dim x factors_dim), but currently has %d x %d."""%
                           (data_dim, factors_dim, in_mat_cxf.shape[0],
                            in_mat_cxf.shape[1]))
      if datasets and 'alignment_bias_c' in datasets[name].keys():
        dataset = datasets[name]
        if hps.do_train_readin:
          print("Initializing trainable readin bias with alignment bias " \
                "provided for dataset:", name)
        else:
          print("Setting non-trainable readin bias to alignment bias " \
                "provided for dataset:", name)
        align_bias_c = dataset['alignment_bias_c'].astype(np.float32)
        align_bias_1xc = np.expand_dims(align_bias_c, axis=0)
        if align_bias_1xc.shape[1] != data_dim:
          raise ValueError("""Alignment bias must have dimensions %d
          (data_dim), but currently has %d."""%
                           (data_dim, in_mat_cxf.shape[0]))
        if in_mat_cxf is not None and align_bias_1xc is not None:
          # (data - alignment_bias) * W_in
          # data * W_in - alignment_bias * W_in
          # So b = -alignment_bias * W_in to accommodate PCA style offset.
          in_bias_1xf = -np.dot(align_bias_1xc, in_mat_cxf)

      if hps.do_train_readin:
          # only add to IO transformations collection only if we want it to be
          # learnable, because IO_transformations collection will be trained
          # when do_train_io_only
          collections_readin=['IO_transformations']
      else:
          collections_readin=None

      in_fac_lin = init_linear(data_dim, used_in_factors_dim,
                               do_bias=True,
                               mat_init_value=in_mat_cxf,
                               bias_init_value=in_bias_1xf,
                               identity_if_possible=in_identity_if_poss,
                               normalized=False, name="x_2_infac_"+name,
                               collections=collections_readin,
                               trainable=hps.do_train_readin)
      in_fac_W, in_fac_b = in_fac_lin
      fns_in_fac_Ws[d] = makelambda(in_fac_W)
      fns_in_fac_bs[d] = makelambda(in_fac_b)

    with tf.variable_scope("glm"):
      out_identity_if_poss = False
      if len(dataset_names) == 1 and \
          factors_dim == hps.dataset_dims[dataset_names[0]]:
        out_identity_if_poss = True
      for d, name in enumerate(dataset_names):
        data_dim = hps.dataset_dims[name]
        in_mat_cxf = None
        if datasets and 'alignment_matrix_cxf' in datasets[name].keys():
          dataset = datasets[name]
          in_mat_cxf = dataset['alignment_matrix_cxf'].astype(np.float32)

        if datasets and 'alignment_bias_c' in datasets[name].keys():
          dataset = datasets[name]
          align_bias_c = dataset['alignment_bias_c'].astype(np.float32)
          align_bias_1xc = np.expand_dims(align_bias_c, axis=0)

        out_mat_fxc = None
        out_bias_1xc = None
        if in_mat_cxf is not None:
            out_mat_fxc = in_mat_cxf.T
        if align_bias_1xc is not None:
          out_bias_1xc = align_bias_1xc

        if hps.output_dist == 'poisson':
          out_fac_lin = init_linear(factors_dim, data_dim, do_bias=True,
                                    mat_init_value=out_mat_fxc,
                                    bias_init_value=out_bias_1xc,
                                    identity_if_possible=out_identity_if_poss,
                                    normalized=False,
                                    name="fac_2_logrates_"+name,
                                    collections=['IO_transformations'])
          out_fac_W, out_fac_b = out_fac_lin

        elif hps.output_dist == 'gaussian':
          out_fac_lin_mean = \
              init_linear(factors_dim, data_dim, do_bias=True,
                          mat_init_value=out_mat_fxc,
                          bias_init_value=out_bias_1xc,
                          normalized=False,
                          name="fac_2_means_"+name,
                          collections=['IO_transformations'])
          out_fac_W_mean, out_fac_b_mean = out_fac_lin_mean

          mat_init_value = np.zeros([factors_dim, data_dim]).astype(np.float32)
          bias_init_value = np.ones([1, data_dim]).astype(np.float32)
          out_fac_lin_logvar = \
              init_linear(factors_dim, data_dim, do_bias=True,
                          mat_init_value=mat_init_value,
                          bias_init_value=bias_init_value,
                          normalized=False,
                          name="fac_2_logvars_"+name,
                          collections=['IO_transformations'])
          out_fac_W_mean, out_fac_b_mean = out_fac_lin_mean
          out_fac_W_logvar, out_fac_b_logvar = out_fac_lin_logvar
          out_fac_W = tf.concat(
              axis=1, values=[out_fac_W_mean, out_fac_W_logvar])
          out_fac_b = tf.concat(
              axis=1, values=[out_fac_b_mean, out_fac_b_logvar])
        else:
          assert False, "NIY"

        preds[d] = tf.equal(tf.constant(name), self.dataName)
        data_dim = hps.dataset_dims[name]
        fns_out_fac_Ws[d] = makelambda(out_fac_W)
        fns_out_fac_bs[d] =  makelambda(out_fac_b)

    pf_pairs_in_fac_Ws = zip(preds, fns_in_fac_Ws)
    pf_pairs_in_fac_bs = zip(preds, fns_in_fac_bs)
    pf_pairs_out_fac_Ws = zip(preds, fns_out_fac_Ws)
    pf_pairs_out_fac_bs = zip(preds, fns_out_fac_bs)

    this_in_fac_W = tf.case(pf_pairs_in_fac_Ws, exclusive=True)
    this_in_fac_b = tf.case(pf_pairs_in_fac_bs, exclusive=True)
    this_out_fac_W = tf.case(pf_pairs_out_fac_Ws, exclusive=True)
    this_out_fac_b = tf.case(pf_pairs_out_fac_bs, exclusive=True)

    # External inputs (not changing by dataset, by definition).
    if hps.ext_input_dim > 0:
      self.ext_input = tf.placeholder(tf.float32,
                                      [None, num_steps, ext_input_dim],
                                      name="ext_input")
    else:
      self.ext_input = None
    ext_input_bxtxi = self.ext_input

    self.keep_prob = keep_prob = tf.placeholder(tf.float32, [], "keep_prob")
    self.batch_size = batch_size = int(hps.batch_size)
    self.learning_rate = tf.Variable(float(hps.learning_rate_init),
                                     trainable=False, name="learning_rate")
    self.learning_rate_decay_op = self.learning_rate.assign(
        self.learning_rate * hps.learning_rate_decay_factor)

    # Dropout the data.
    dataset_do_bxtxd = tf.nn.dropout(tf.to_float(dataset_ph), keep_prob)
    if hps.ext_input_dim > 0:
      ext_input_do_bxtxi = tf.nn.dropout(ext_input_bxtxi, keep_prob)
    else:
      ext_input_do_bxtxi = None

    # ENCODERS
    def encode_data(dataset_bxtxd, enc_cell, name, forward_or_reverse,
                num_steps_to_encode):
      """Encode data for LFADS
      Args:
        dataset_bxtxd - the data to encode, as a 3 tensor, with dims
          time x batch x data dims.
        enc_cell: encoder cell
        name: name of encoder
        forward_or_reverse: string, encode in forward or reverse direction
        num_steps_to_encode: number of steps to  encode, 0:num_steps_to_encode
      Returns:
        encoded data as a list with num_steps_to_encode items, in order
      """
      if forward_or_reverse == "forward":
        dstr = "_fwd"
        time_fwd_or_rev = range(num_steps_to_encode)
      else:
        dstr = "_rev"
        time_fwd_or_rev = reversed(range(num_steps_to_encode))

      with tf.variable_scope(name+"_enc"+dstr, reuse=False):
        enc_state = tf.tile(
            tf.Variable(tf.zeros([1, enc_cell.state_size]),
                        name=name+"_enc_t0"+dstr), tf.stack([batch_size, 1]))
        enc_state.set_shape([None, enc_cell.state_size]) # tile loses shape

      enc_outs = [None] * num_steps_to_encode
      for i, t in enumerate(time_fwd_or_rev):
        with tf.variable_scope(name+"_enc"+dstr, reuse=True if i > 0 else None):
          dataset_t_bxd = dataset_bxtxd[:,t,:]
          in_fac_t_bxf = tf.matmul(dataset_t_bxd, this_in_fac_W) + this_in_fac_b
          in_fac_t_bxf.set_shape([None, used_in_factors_dim])
          if ext_input_dim > 0 and not hps.inject_ext_input_to_gen:
            ext_input_t_bxi = ext_input_do_bxtxi[:,t,:]
            enc_input_t_bxfpe = tf.concat(
                axis=1, values=[in_fac_t_bxf, ext_input_t_bxi])
          else:
            enc_input_t_bxfpe = in_fac_t_bxf
          enc_out, enc_state = enc_cell(enc_input_t_bxfpe, enc_state)
          enc_outs[t] = enc_out

      return enc_outs

    # Encode initial condition means and variances
    # ([x_T, x_T-1, ... x_0] and [x_0, x_1, ... x_T] -> g0/c0)
    self.ic_enc_fwd = [None] * num_steps
    self.ic_enc_rev = [None] * num_steps
    if ic_dim > 0:
      enc_ic_cell = cell_class(hps.ic_enc_dim,
                               weight_scale=hps.cell_weight_scale,
                               clip_value=hps.cell_clip_value)
      ic_enc_fwd = encode_data(dataset_do_bxtxd, enc_ic_cell,
                               "ic", "forward",
                               hps.num_steps_for_gen_ic)
      ic_enc_rev = encode_data(dataset_do_bxtxd, enc_ic_cell,
                               "ic", "reverse",
                               hps.num_steps_for_gen_ic)
      self.ic_enc_fwd = ic_enc_fwd
      self.ic_enc_rev = ic_enc_rev

    # Encoder control input means and variances, bi-directional encoding so:
    # ([x_T, x_T-1, ..., x_0] and [x_0, x_1 ... x_T] -> u_t)
    self.ci_enc_fwd = [None] * num_steps
    self.ci_enc_rev = [None] * num_steps
    if co_dim > 0:
      enc_ci_cell = cell_class(hps.ci_enc_dim,
                               weight_scale=hps.cell_weight_scale,
                               clip_value=hps.cell_clip_value)
      ci_enc_fwd = encode_data(dataset_do_bxtxd, enc_ci_cell,
                               "ci", "forward",
                               hps.num_steps)
      if hps.do_causal_controller:
        ci_enc_rev = None
      else:
        ci_enc_rev = encode_data(dataset_do_bxtxd, enc_ci_cell,
                                 "ci", "reverse",
                                 hps.num_steps)
      self.ci_enc_fwd = ci_enc_fwd
      self.ci_enc_rev = ci_enc_rev

    # STOCHASTIC LATENT VARIABLES, priors and posteriors
    # (initial conditions g0, and control inputs, u_t)
    # Note that zs represent all the stochastic latent variables.
    with tf.variable_scope("z", reuse=False):
      self.prior_zs_g0 = None
      self.posterior_zs_g0 = None
      self.g0s_val = None
      if ic_dim > 0:
        self.prior_zs_g0 = \
            LearnableDiagonalGaussian(batch_size, ic_dim, name="prior_g0",
                                      mean_init=0.0,
                                      var_min=hps.ic_prior_var_min,
                                      var_init=hps.ic_prior_var_scale,
                                      var_max=hps.ic_prior_var_max)
        ic_enc = tf.concat(axis=1, values=[ic_enc_fwd[-1], ic_enc_rev[0]])
        ic_enc = tf.nn.dropout(ic_enc, keep_prob)
        self.posterior_zs_g0 = \
            DiagonalGaussianFromInput(ic_enc, ic_dim, "ic_enc_2_post_g0",
                                      var_min=hps.ic_post_var_min)
        if kind in ["train", "posterior_sample_and_average",
                    "posterior_push_mean"]:
          zs_g0 = self.posterior_zs_g0
        else:
          zs_g0 = self.prior_zs_g0
        if kind in ["train", "posterior_sample_and_average", "prior_sample"]:
          self.g0s_val = zs_g0.sample
        else:
          self.g0s_val = zs_g0.mean

      # Priors for controller, 'co' for controller output
      self.prior_zs_co = prior_zs_co = [None] * num_steps
      self.posterior_zs_co = posterior_zs_co = [None] * num_steps
      self.zs_co = zs_co = [None] * num_steps
      self.prior_zs_ar_con = None
      if co_dim > 0:
        # Controller outputs
        autocorrelation_taus = [hps.prior_ar_atau for x in range(hps.co_dim)]
        noise_variances = [hps.prior_ar_nvar for x in range(hps.co_dim)]
        self.prior_zs_ar_con = prior_zs_ar_con = \
            LearnableAutoRegressive1Prior(batch_size, hps.co_dim,
                                          autocorrelation_taus,
                                          noise_variances,
                                          hps.do_train_prior_ar_atau,
                                          hps.do_train_prior_ar_nvar,
                                          num_steps, "u_prior_ar1")

    # CONTROLLER -> GENERATOR -> RATES
    # (u(t) -> gen(t) -> factors(t) -> rates(t) -> p(x_t|z_t) )
    self.controller_outputs = u_t = [None] * num_steps
    self.con_ics = con_state = None
    self.con_states = con_states = [None] * num_steps
    self.con_outs = con_outs = [None] * num_steps
    self.gen_inputs = gen_inputs = [None] * num_steps
    if co_dim > 0:
      # gen_cell_class here for l2 penalty recurrent weights
      # didn't split the cell_weight scale here, because I doubt it matters
      con_cell = gen_cell_class(hps.con_dim,
                                input_weight_scale=hps.cell_weight_scale,
                                rec_weight_scale=hps.cell_weight_scale,
                                clip_value=hps.cell_clip_value,
                                recurrent_collections=['l2_con_reg'])
      with tf.variable_scope("con", reuse=False):
        self.con_ics = tf.tile(
            tf.Variable(tf.zeros([1, hps.con_dim*con_cell.state_multiplier]),
                        name="c0"),
            tf.stack([batch_size, 1]))
        self.con_ics.set_shape([None, con_cell.state_size]) # tile loses shape
        con_states[-1] = self.con_ics

    gen_cell = gen_cell_class(hps.gen_dim,
                              input_weight_scale=hps.gen_cell_input_weight_scale,
                              rec_weight_scale=hps.gen_cell_rec_weight_scale,
                              clip_value=hps.cell_clip_value,
                              recurrent_collections=['l2_gen_reg'])
    with tf.variable_scope("gen", reuse=False):
      if ic_dim == 0:
        self.gen_ics = tf.tile(
              tf.Variable(tf.zeros([1, gen_cell.state_size]), name="g0"),
              tf.stack([batch_size, 1]))
      else:
        self.gen_ics = linear(self.g0s_val, gen_cell.state_size,
                              identity_if_possible=True,
                              name="g0_2_gen_ic")

      self.gen_states = gen_states = [None] * num_steps
      self.gen_outs = gen_outs = [None] * num_steps
      gen_states[-1] = self.gen_ics
      gen_outs[-1] = gen_cell.output_from_state(gen_states[-1])
      self.factors = factors = [None] * num_steps
      factors[-1] = linear(gen_outs[-1], factors_dim, do_bias=False,
                           normalized=True, name="gen_2_fac")

    self.rates = rates = [None] * num_steps
    # rates[-1] is collected to potentially feed back to controller
    with tf.variable_scope("glm", reuse=False):
      if hps.output_dist == 'poisson':
        log_rates_t0 = tf.matmul(factors[-1], this_out_fac_W) + this_out_fac_b
        log_rates_t0.set_shape([None, None])
        rates[-1] = tf.exp(log_rates_t0) # rate
        rates[-1].set_shape([None, hps.dataset_dims[hps.dataset_names[0]]])
      elif hps.output_dist == 'gaussian':
        mean_n_logvars = tf.matmul(factors[-1],this_out_fac_W) + this_out_fac_b
        mean_n_logvars.set_shape([None, None])
        means_t_bxd, logvars_t_bxd = tf.split(axis=1, num_or_size_splits=2,
                                              value=mean_n_logvars)
        rates[-1] = means_t_bxd
      else:
        assert False, "NIY"

    # We support multiple output distributions, for example Poisson, and also
    # Gaussian. In these two cases respectively, there are one and two
    # parameters (rates vs. mean and variance).  So the output_dist_params
    # tensor will variable sizes via tf.concat and tf.split, along the 1st
    # dimension. So in the case of gaussian, for example, it'll be
    # batch x (D+D), where each D dims is the mean, and then variances,
    # respectively. For a distribution with 3 parameters, it would be
    # batch x (D+D+D).
    self.output_dist_params = dist_params = [None] * num_steps
    self.log_p_xgz_b = log_p_xgz_b = 0.0  # log P(x|z)
    for t in range(num_steps):
      # Controller
      if co_dim > 0:
        # Build inputs for controller
        tlag = t - hps.controller_input_lag
        if tlag < 0:
          con_in_f_t = tf.zeros_like(ci_enc_fwd[0])
        else:
          con_in_f_t = ci_enc_fwd[tlag]
        if hps.do_causal_controller:
          # If controller is causal (wrt to data generation process), then it
          # cannot see future data.  Thus, excluding ci_enc_rev[t] is obvious.
          # Less obvious is the need to exclude factors[t-1].  This arises
          # because information flows from g0 through factors to the controller
          # input.  The g0 encoding is backwards, so we must necessarily exclude
          # the factors in order to keep the controller input purely from a
          # forward encoding (however unlikely it is that
          # g0->factors->controller channel might actually be used in this way).
          con_in_list_t = [con_in_f_t]
        else:
          tlag_rev = t + hps.controller_input_lag
          if tlag_rev >= num_steps:
            # better than zeros
            con_in_r_t = tf.zeros_like(ci_enc_rev[0])
          else:
            con_in_r_t = ci_enc_rev[tlag_rev]
          con_in_list_t = [con_in_f_t, con_in_r_t]

        if hps.do_feed_factors_to_controller:
          if hps.feedback_factors_or_rates == "factors":
            con_in_list_t.append(factors[t-1])
          elif hps.feedback_factors_or_rates == "rates":
            con_in_list_t.append(rates[t-1])
          else:
            assert False, "NIY"

        con_in_t = tf.concat(axis=1, values=con_in_list_t)
        con_in_t = tf.nn.dropout(con_in_t, keep_prob)
        with tf.variable_scope("con", reuse=True if t > 0 else None):
          con_outs[t], con_states[t] = con_cell(con_in_t, con_states[t-1])
          posterior_zs_co[t] = \
            DiagonalGaussianFromInput(con_outs[t], co_dim,
                                      name="con_to_post_co")
        if kind == "train":
          u_t[t] = posterior_zs_co[t].sample
        elif kind == "posterior_sample_and_average":
          u_t[t] = posterior_zs_co[t].sample
        elif kind == "posterior_push_mean":
          u_t[t] = posterior_zs_co[t].mean
        else:
          u_t[t] = prior_zs_ar_con.samples_t[t]

      # Inputs to the generator (controller output + external input)
      if ext_input_dim > 0 and hps.inject_ext_input_to_gen:
        ext_input_t_bxi = ext_input_do_bxtxi[:,t,:]
        if co_dim > 0:
          gen_inputs[t] = tf.concat(axis=1, values=[u_t[t], ext_input_t_bxi])
        else:
          gen_inputs[t] = ext_input_t_bxi
      else:
        gen_inputs[t] = u_t[t]

      # Generator
      data_t_bxd = dataset_ph[:,t,:]
      with tf.variable_scope("gen", reuse=True if t > 0 else None):
        gen_outs[t], gen_states[t] = gen_cell(gen_inputs[t], gen_states[t-1])
        gen_outs[t] = tf.nn.dropout(gen_outs[t], keep_prob)
      with tf.variable_scope("gen", reuse=True): # ic defined it above
        factors[t] = linear(gen_outs[t], factors_dim, do_bias=False,
                            normalized=True, name="gen_2_fac")
      with tf.variable_scope("glm", reuse=True if t > 0 else None):
        if hps.output_dist == 'poisson':
          log_rates_t = tf.matmul(factors[t], this_out_fac_W) + this_out_fac_b
          log_rates_t.set_shape([None, None])
          rates[t] = dist_params[t] = tf.exp(tf.clip_by_value(log_rates_t, -hps._clip_value, hps._clip_value)) # rates feed back
          rates[t].set_shape([None, hps.dataset_dims[hps.dataset_names[0]]])
          loglikelihood_t = Poisson(log_rates_t).logp(data_t_bxd)

        elif hps.output_dist == 'gaussian':
          mean_n_logvars = tf.matmul(factors[t],this_out_fac_W) + this_out_fac_b
          mean_n_logvars.set_shape([None, None])
          means_t_bxd, logvars_t_bxd = tf.split(axis=1, num_or_size_splits=2,
                                                value=mean_n_logvars)
          rates[t] = means_t_bxd # rates feed back to controller
          dist_params[t] = tf.concat(
              axis=1, values=[means_t_bxd, tf.exp(tf.clip_by_value(logvars_t_bxd, -hps._clip_value, hps._clip_value))])
          loglikelihood_t = \
              diag_gaussian_log_likelihood(data_t_bxd,
                                           means_t_bxd, logvars_t_bxd)
        else:
          assert False, "NIY"

        log_p_xgz_b += tf.reduce_sum(loglikelihood_t, [1])

    # Correlation of inferred inputs cost.
    self.corr_cost = tf.constant(0.0)
    if hps.co_mean_corr_scale > 0.0:
      all_sum_corr = []
      for i in range(hps.co_dim):
        for j in range(i+1, hps.co_dim):
          sum_corr_ij = tf.constant(0.0)
          for t in range(num_steps):
            u_mean_t = posterior_zs_co[t].mean
            sum_corr_ij += u_mean_t[:,i]*u_mean_t[:,j]
          all_sum_corr.append(0.5 * tf.square(sum_corr_ij))
      self.corr_cost = tf.reduce_mean(all_sum_corr) # div by batch and by n*(n-1)/2 pairs

    # Variational Lower Bound on posterior, p(z|x), plus reconstruction cost.
    # KL and reconstruction costs are normalized only by batch size, not by
    # dimension, or by time steps.
    kl_cost_g0_b = tf.zeros_like(batch_size, dtype=tf.float32)
    kl_cost_co_b = tf.zeros_like(batch_size, dtype=tf.float32)
    self.kl_cost = tf.constant(0.0) # VAE KL cost
    self.recon_cost = tf.constant(0.0) # VAE reconstruction cost
    self.nll_bound_vae = tf.constant(0.0)
    self.nll_bound_iwae = tf.constant(0.0) # for eval with IWAE cost.
    if kind in ["train", "posterior_sample_and_average", "posterior_push_mean"]:
      kl_cost_g0_b = 0.0
      kl_cost_co_b = 0.0
      if ic_dim > 0:
        g0_priors = [self.prior_zs_g0]
        g0_posts = [self.posterior_zs_g0]
        kl_cost_g0_b = KLCost_GaussianGaussian(g0_posts, g0_priors).kl_cost_b
        kl_cost_g0_b = hps.kl_ic_weight * kl_cost_g0_b
      if co_dim > 0:
        kl_cost_co_b = \
            KLCost_GaussianGaussianProcessSampled(
                posterior_zs_co, prior_zs_ar_con).kl_cost_b
        kl_cost_co_b = hps.kl_co_weight * kl_cost_co_b

      # L = -KL + log p(x|z), to maximize bound on likelihood
      # -L = KL - log p(x|z), to minimize bound on NLL
      # so 'reconstruction cost' is negative log likelihood
      self.recon_cost = - tf.reduce_mean(log_p_xgz_b)
      self.kl_cost = tf.reduce_mean(kl_cost_g0_b + kl_cost_co_b)

      lb_on_ll_b = log_p_xgz_b - kl_cost_g0_b - kl_cost_co_b

      # VAE error averages outside the log
      self.nll_bound_vae = -tf.reduce_mean(lb_on_ll_b)

      # IWAE error averages inside the log
      k = tf.cast(tf.shape(log_p_xgz_b)[0], tf.float32)
      iwae_lb_on_ll = -tf.log(k) + log_sum_exp(lb_on_ll_b)
      self.nll_bound_iwae = -iwae_lb_on_ll

    # L2 regularization on the generator, normalized by number of parameters.
    self.l2_cost = tf.constant(0.0)
    if self.hps.l2_gen_scale > 0.0 or self.hps.l2_con_scale > 0.0:
      l2_costs = []
      l2_numels = []
      l2_reg_var_lists = [tf.get_collection('l2_gen_reg'),
                          tf.get_collection('l2_con_reg')]
      l2_reg_scales = [self.hps.l2_gen_scale, self.hps.l2_con_scale]
      for l2_reg_vars, l2_scale in zip(l2_reg_var_lists, l2_reg_scales):
        for v in l2_reg_vars:
          numel = tf.reduce_prod(tf.concat(axis=0, values=tf.shape(v)))
          numel_f = tf.cast(numel, tf.float32)
          l2_numels.append(numel_f)
          v_l2 = tf.reduce_sum(v*v)
          l2_costs.append(0.5 * l2_scale * v_l2)
      self.l2_cost = tf.add_n(l2_costs) / tf.add_n(l2_numels)

    # Compute the cost for training, part of the graph regardless.
    # The KL cost can be problematic at the beginning of optimization,
    # so we allow an exponential increase in weighting the KL from 0
    # to 1.
    self.kl_decay_step = tf.maximum(self.train_step - hps.kl_start_step, 0)
    self.l2_decay_step = tf.maximum(self.train_step - hps.l2_start_step, 0)
    kl_decay_step_f = tf.cast(self.kl_decay_step, tf.float32)
    l2_decay_step_f = tf.cast(self.l2_decay_step, tf.float32)
    kl_increase_steps_f = tf.cast(hps.kl_increase_steps, tf.float32)
    l2_increase_steps_f = tf.cast(hps.l2_increase_steps, tf.float32)
    self.kl_weight = kl_weight = \
        tf.minimum(kl_decay_step_f / kl_increase_steps_f, 1.0)
    self.l2_weight = l2_weight = \
        tf.minimum(l2_decay_step_f / l2_increase_steps_f, 1.0)

    self.timed_kl_cost = kl_weight * self.kl_cost
    self.timed_l2_cost = l2_weight * self.l2_cost
    self.weight_corr_cost = hps.co_mean_corr_scale * self.corr_cost
    self.cost = self.recon_cost + self.timed_kl_cost + \
        self.timed_l2_cost + self.weight_corr_cost

    if kind != "train":
      # save every so often
      self.seso_saver = tf.train.Saver(tf.global_variables(),
                                      max_to_keep=hps.max_ckpt_to_keep)
      # lowest validation error
      self.lve_saver = tf.train.Saver(tf.global_variables(),
                                      max_to_keep=hps.max_ckpt_to_keep_lve)

      return

    # OPTIMIZATION
    # train the io matrices only
    if self.hps.do_train_io_only:
      self.train_vars = tvars = \
        tf.get_collection('IO_transformations',
                          scope=tf.get_variable_scope().name)
    # train the encoder only
    elif self.hps.do_train_encoder_only:
      tvars1 = \
        tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,
                          scope='LFADS/ic_enc_*')
      tvars2 = \
        tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,
                          scope='LFADS/z/ic_enc_*')

      self.train_vars = tvars = tvars1 + tvars2
    # train all variables
    else:
      self.train_vars = tvars = \
        tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,
                          scope=tf.get_variable_scope().name)
    print("done.")
    print("Model Variables (to be optimized): ")
    total_params = 0
    for i in range(len(tvars)):
      shape = tvars[i].get_shape().as_list()
      print("    ", i, tvars[i].name, shape)
      total_params += np.prod(shape)
    print("Total model parameters: ", total_params)

    grads = tf.gradients(self.cost, tvars)
    grads, grad_global_norm = tf.clip_by_global_norm(grads, hps.max_grad_norm)
    opt = tf.train.AdamOptimizer(self.learning_rate, beta1=0.9, beta2=0.999,
                                 epsilon=1e-01)
    self.grads = grads
    self.grad_global_norm = grad_global_norm
    self.train_op = opt.apply_gradients(
        zip(grads, tvars), global_step=self.train_step)

    self.seso_saver = tf.train.Saver(tf.global_variables(),
                                    max_to_keep=hps.max_ckpt_to_keep)

    # lowest validation error
    self.lve_saver = tf.train.Saver(tf.global_variables(),
                                    max_to_keep=hps.max_ckpt_to_keep)

    # SUMMARIES, used only during training.
    # example summary
    self.example_image = tf.placeholder(tf.float32, shape=[1,None,None,3],
                                        name='image_tensor')
    self.example_summ = tf.summary.image("LFADS example", self.example_image,
                                        collections=["example_summaries"])

    # general training summaries
    self.lr_summ = tf.summary.scalar("Learning rate", self.learning_rate)
    self.kl_weight_summ = tf.summary.scalar("KL weight", self.kl_weight)
    self.l2_weight_summ = tf.summary.scalar("L2 weight", self.l2_weight)
    self.corr_cost_summ = tf.summary.scalar("Corr cost", self.weight_corr_cost)
    self.grad_global_norm_summ = tf.summary.scalar("Gradient global norm",
                                                   self.grad_global_norm)
    if hps.co_dim > 0:
      self.atau_summ = [None] * hps.co_dim
      self.pvar_summ = [None] * hps.co_dim
      for c in range(hps.co_dim):
        self.atau_summ[c] = \
            tf.summary.scalar("AR Autocorrelation taus " + str(c),
                              tf.exp(self.prior_zs_ar_con.logataus_1xu[0,c]))
        self.pvar_summ[c] = \
            tf.summary.scalar("AR Variances " + str(c),
                              tf.exp(self.prior_zs_ar_con.logpvars_1xu[0,c]))

    # cost summaries, separated into different collections for
    # training vs validation.  We make placeholders for these, because
    # even though the graph computes these costs on a per-batch basis,
    # we want to report the more reliable metric of per-epoch cost.
    kl_cost_ph = tf.placeholder(tf.float32, shape=[], name='kl_cost_ph')
    self.kl_t_cost_summ = tf.summary.scalar("KL cost (train)", kl_cost_ph,
                                            collections=["train_summaries"])
    self.kl_v_cost_summ = tf.summary.scalar("KL cost (valid)", kl_cost_ph,
                                            collections=["valid_summaries"])
    l2_cost_ph = tf.placeholder(tf.float32, shape=[], name='l2_cost_ph')
    self.l2_cost_summ = tf.summary.scalar("L2 cost", l2_cost_ph,
                                          collections=["train_summaries"])

    recon_cost_ph = tf.placeholder(tf.float32, shape=[], name='recon_cost_ph')
    self.recon_t_cost_summ = tf.summary.scalar("Reconstruction cost (train)",
                                               recon_cost_ph,
                                               collections=["train_summaries"])
    self.recon_v_cost_summ = tf.summary.scalar("Reconstruction cost (valid)",
                                               recon_cost_ph,
                                               collections=["valid_summaries"])

    total_cost_ph = tf.placeholder(tf.float32, shape=[], name='total_cost_ph')
    self.cost_t_summ = tf.summary.scalar("Total cost (train)", total_cost_ph,
                                         collections=["train_summaries"])
    self.cost_v_summ = tf.summary.scalar("Total cost (valid)", total_cost_ph,
                                         collections=["valid_summaries"])

    self.kl_cost_ph = kl_cost_ph
    self.l2_cost_ph = l2_cost_ph
    self.recon_cost_ph = recon_cost_ph
    self.total_cost_ph = total_cost_ph

    # Merged summaries, for easy coding later.
    self.merged_examples = tf.summary.merge_all(key="example_summaries")
    self.merged_generic = tf.summary.merge_all() # default key is 'summaries'
    self.merged_train = tf.summary.merge_all(key="train_summaries")
    self.merged_valid = tf.summary.merge_all(key="valid_summaries")

    session = tf.get_default_session()
    self.logfile = os.path.join(hps.lfads_save_dir, "lfads_log")
    self.writer = tf.summary.FileWriter(self.logfile)