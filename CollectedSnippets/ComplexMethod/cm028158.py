def add_alignment_projections(datasets, npcs, ntime=None, nsamples=None):
  """Create a matrix that aligns the datasets a bit, under
  the assumption that each dataset is observing the same underlying dynamical
  system.

  Args:
    datasets: The dictionary of dataset structures.
    npcs:  The number of pcs for each, basically like lfads factors.
    nsamples (optional): Number of samples to take for each dataset.
    ntime (optional): Number of time steps to take in each sample.

  Returns:
    The dataset structures, with the field alignment_matrix_cxf added.
    This is # channels x npcs dimension
"""
  nchannels_all = 0
  channel_idxs = {}
  conditions_all = {}
  nconditions_all = 0
  for name, dataset in datasets.items():
    cidxs = np.where(dataset['P_sxn'])[1] # non-zero entries in columns
    channel_idxs[name] = [cidxs[0], cidxs[-1]+1]
    nchannels_all += cidxs[-1]+1 - cidxs[0]
    conditions_all[name] = np.unique(dataset['condition_labels_train'])

  all_conditions_list = \
      np.unique(np.ndarray.flatten(np.array(conditions_all.values())))
  nconditions_all = all_conditions_list.shape[0]

  if ntime is None:
    ntime = dataset['train_data'].shape[1]
  if nsamples is None:
    nsamples = dataset['train_data'].shape[0]

  # In the data workup in the paper, Chethan did intra condition
  # averaging, so let's do that here.
  avg_data_all = {}
  for name, conditions in conditions_all.items():
    dataset = datasets[name]
    avg_data_all[name] = {}
    for cname in conditions:
      td_idxs = np.argwhere(np.array(dataset['condition_labels_train'])==cname)
      data = np.squeeze(dataset['train_data'][td_idxs,:,:], axis=1)
      avg_data = np.mean(data, axis=0)
      avg_data_all[name][cname] = avg_data

  # Visualize this in the morning.
  all_data_nxtc = np.zeros([nchannels_all, ntime * nconditions_all])
  for name, dataset in datasets.items():
    cidx_s = channel_idxs[name][0]
    cidx_f = channel_idxs[name][1]
    for cname in conditions_all[name]:
      cidxs = np.argwhere(all_conditions_list == cname)
      if cidxs.shape[0] > 0:
        cidx = cidxs[0][0]
        all_tidxs = np.arange(0, ntime+1) + cidx*ntime
        all_data_nxtc[cidx_s:cidx_f, all_tidxs[0]:all_tidxs[-1]] = \
            avg_data_all[name][cname].T

  # A bit of filtering. We don't care about spectral properties, or
  # filtering artifacts, simply correlate time steps a bit.
  filt_len = 6
  bc_filt = np.ones([filt_len])/float(filt_len)
  for c in range(nchannels_all):
    all_data_nxtc[c,:] = scipy.signal.filtfilt(bc_filt, [1.0], all_data_nxtc[c,:])

  # Compute the PCs.
  all_data_mean_nx1 = np.mean(all_data_nxtc, axis=1, keepdims=True)
  all_data_zm_nxtc = all_data_nxtc - all_data_mean_nx1
  corr_mat_nxn = np.dot(all_data_zm_nxtc, all_data_zm_nxtc.T)
  evals_n, evecs_nxn = np.linalg.eigh(corr_mat_nxn)
  sidxs = np.flipud(np.argsort(evals_n)) # sort such that 0th is highest
  evals_n = evals_n[sidxs]
  evecs_nxn = evecs_nxn[:,sidxs]

  # Project all the channels data onto the low-D PCA basis, where
  # low-d is the npcs parameter.
  all_data_pca_pxtc = np.dot(evecs_nxn[:, 0:npcs].T, all_data_zm_nxtc)

  # Now for each dataset, we regress the channel data onto the top
  # pcs, and this will be our alignment matrix for that dataset.
  # |B - A*W|^2
  for name, dataset in datasets.items():
    cidx_s = channel_idxs[name][0]
    cidx_f = channel_idxs[name][1]
    all_data_zm_chxtc = all_data_zm_nxtc[cidx_s:cidx_f,:] # ch for channel
    W_chxp, _, _, _ = \
        np.linalg.lstsq(all_data_zm_chxtc.T, all_data_pca_pxtc.T)
    dataset['alignment_matrix_cxf'] = W_chxp
    alignment_bias_cx1 = all_data_mean_nx1[cidx_s:cidx_f]
    dataset['alignment_bias_c'] = np.squeeze(alignment_bias_cx1, axis=1)

  do_debug_plot = False
  if do_debug_plot:
    pc_vecs = evecs_nxn[:,0:npcs]
    ntoplot = 400

    plt.figure()
    plt.plot(np.log10(evals_n), '-x')
    plt.figure()
    plt.subplot(311)
    plt.imshow(all_data_pca_pxtc)
    plt.colorbar()

    plt.subplot(312)
    plt.imshow(np.dot(W_chxp.T, all_data_zm_chxtc))
    plt.colorbar()

    plt.subplot(313)
    plt.imshow(np.dot(all_data_zm_chxtc.T, W_chxp).T - all_data_pca_pxtc)
    plt.colorbar()

    import pdb
    pdb.set_trace()

  return datasets