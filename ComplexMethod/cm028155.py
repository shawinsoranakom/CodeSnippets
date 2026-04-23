def plot_lfads_timeseries(data_bxtxn, model_vals, ext_input_bxtxi=None,
                          truth_bxtxn=None, bidx=None, output_dist="poisson",
                          conversion_factor=1.0, subplot_cidx=0,
                          col_title=None):

  n_to_plot = 10
  scale = 1.0
  nrows = 7
  plt.subplot(nrows,2,1+subplot_cidx)

  if output_dist == 'poisson':
    rates = means = conversion_factor * model_vals['output_dist_params']
    plot_time_series(rates, bidx, n_to_plot=n_to_plot, scale=scale,
                     title=col_title + " rates (LFADS - red, Truth - black)")
  elif output_dist == 'gaussian':
    means_vars = model_vals['output_dist_params']
    means, vars = np.split(means_vars,2, axis=2) # bxtxn
    stds = np.sqrt(vars)
    plot_time_series(means, bidx, n_to_plot=n_to_plot, scale=scale,
                     title=col_title + " means (LFADS - red, Truth - black)")
    plot_time_series(means+stds, bidx, n_to_plot=n_to_plot, scale=scale,
                     color='c')
    plot_time_series(means-stds, bidx, n_to_plot=n_to_plot, scale=scale,
                     color='c')
  else:
    assert 'NIY'


  if truth_bxtxn is not None:
    plot_time_series(truth_bxtxn, bidx, n_to_plot=n_to_plot, color='k',
                     scale=scale)

  input_title = ""
  if "controller_outputs" in model_vals.keys():
    input_title += " Controller Output"
    plt.subplot(nrows,2,3+subplot_cidx)
    u_t = model_vals['controller_outputs'][0:-1]
    plot_time_series(u_t, bidx, n_to_plot=n_to_plot, color='c', scale=1.0,
                     title=col_title + input_title)

  if ext_input_bxtxi is not None:
    input_title += " External Input"
    plot_time_series(ext_input_bxtxi, n_to_plot=n_to_plot, color='b',
                     scale=scale, title=col_title + input_title)

  plt.subplot(nrows,2,5+subplot_cidx)
  plot_time_series(means, bidx,
                   n_to_plot=n_to_plot, scale=1.0,
                   title=col_title + " Spikes (LFADS - red, Spikes - black)")
  plot_time_series(data_bxtxn, bidx, n_to_plot=n_to_plot, color='k', scale=1.0)

  plt.subplot(nrows,2,7+subplot_cidx)
  plot_time_series(model_vals['factors'], bidx, n_to_plot=n_to_plot, color='b',
                   scale=2.0, title=col_title + " Factors")

  plt.subplot(nrows,2,9+subplot_cidx)
  plot_time_series(model_vals['gen_states'], bidx, n_to_plot=n_to_plot,
                   color='g', scale=1.0, title=col_title + " Generator State")

  if bidx is not None:
    data_nxt = data_bxtxn[bidx,:,:].T
    params_nxt = model_vals['output_dist_params'][bidx,:,:].T
  else:
    data_nxt = np.mean(data_bxtxn, axis=0).T
    params_nxt = np.mean(model_vals['output_dist_params'], axis=0).T
  if output_dist == 'poisson':
    means_nxt = params_nxt
  elif output_dist == 'gaussian': # (means+vars) x time
    means_nxt = np.vsplit(params_nxt,2)[0] # get means
  else:
    assert "NIY"

  plt.subplot(nrows,2,11+subplot_cidx)
  plt.imshow(data_nxt, aspect='auto', interpolation='nearest')
  plt.title(col_title + ' Data')

  plt.subplot(nrows,2,13+subplot_cidx)
  plt.imshow(means_nxt, aspect='auto', interpolation='nearest')
  plt.title(col_title + ' Means')