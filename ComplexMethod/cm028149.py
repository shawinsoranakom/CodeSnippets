def train_model(self, datasets):
    """Train the model, print per-epoch information, and save checkpoints.

    Loop over training epochs. The function that actually does the
    training is train_epoch.  This function iterates over the training
    data, one epoch at a time.  The learning rate schedule is such
    that it will stay the same until the cost goes up in comparison to
    the last few values, then it will drop.

    Args:
      datasets: A dict of data dicts.  The dataset dict is simply a
        name(string)-> data dictionary mapping (See top of lfads.py).
    """
    hps = self.hps
    has_any_valid_set = False
    for data_dict in datasets.values():
      if data_dict['valid_data'] is not None:
        has_any_valid_set = True
        break

    session = tf.get_default_session()
    lr = session.run(self.learning_rate)
    lr_stop = hps.learning_rate_stop
    i = -1
    train_costs = []
    valid_costs = []
    ev_total_cost = ev_recon_cost = ev_kl_cost = 0.0
    lowest_ev_cost = np.Inf
    while True:
      i += 1
      do_save_ckpt = True if i % 10 ==0 else False
      tr_total_cost, tr_recon_cost, tr_kl_cost, kl_weight, l2_cost, l2_weight = \
                self.train_epoch(datasets, do_save_ckpt=do_save_ckpt)

      # Evaluate the validation cost, and potentially save.  Note that this
      # routine will not save a validation checkpoint until the kl weight and
      # l2 weights are equal to 1.0.
      if has_any_valid_set:
        ev_total_cost, ev_recon_cost, ev_kl_cost = \
            self.eval_cost_epoch(datasets, kind='valid')
        valid_costs.append(ev_total_cost)

        # > 1 may give more consistent results, but not the actual lowest vae.
        # == 1 gives the lowest vae seen so far.
        n_lve = 1
        run_avg_lve = np.mean(valid_costs[-n_lve:])

        # conditions for saving checkpoints:
        #   KL weight must have finished stepping (>=1.0), AND
        #   L2 weight must have finished stepping OR L2 is not being used, AND
        #   the current run has a lower LVE than previous runs AND
        #     len(valid_costs > n_lve) (not sure what that does)
        if kl_weight >= 1.0 and \
          (l2_weight >= 1.0 or \
           (self.hps.l2_gen_scale == 0.0 and self.hps.l2_con_scale == 0.0)) \
           and (len(valid_costs) > n_lve and run_avg_lve < lowest_ev_cost):

          lowest_ev_cost = run_avg_lve
          checkpoint_path = os.path.join(self.hps.lfads_save_dir,
                                         self.hps.checkpoint_name + '_lve.ckpt')
          self.lve_saver.save(session, checkpoint_path,
                              global_step=self.train_step,
                              latest_filename='checkpoint_lve')

      # Plot and summarize.
      values = {'nepochs':i, 'has_any_valid_set': has_any_valid_set,
                'tr_total_cost':tr_total_cost, 'ev_total_cost':ev_total_cost,
                'tr_recon_cost':tr_recon_cost, 'ev_recon_cost':ev_recon_cost,
                'tr_kl_cost':tr_kl_cost, 'ev_kl_cost':ev_kl_cost,
                'l2_weight':l2_weight, 'kl_weight':kl_weight,
                'l2_cost':l2_cost}
      self.summarize_all(datasets, values)
      self.plot_single_example(datasets)

      # Manage learning rate.
      train_res = tr_total_cost
      n_lr = hps.learning_rate_n_to_compare
      if len(train_costs) > n_lr and train_res > np.max(train_costs[-n_lr:]):
        _ = session.run(self.learning_rate_decay_op)
        lr = session.run(self.learning_rate)
        print("     Decreasing learning rate to %f." % lr)
        # Force the system to run n_lr times while at this lr.
        train_costs.append(np.inf)
      else:
        train_costs.append(train_res)

      if lr < lr_stop:
        print("Stopping optimization based on learning rate criteria.")
        break