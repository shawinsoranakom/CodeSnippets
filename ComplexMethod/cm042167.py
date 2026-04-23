def get_eps_factor(lr, plot=False):
  engaged = False
  steering_pressed = False
  torque_cmd, eps_torque = None, None
  cmds, eps = [], []

  for msg in lr:
    if msg.which() != 'can':
      continue

    for m in msg.can:
      if m.address == 0x2e4 and m.src == 128:
        engaged = bool(m.dat[0] & 1)
        torque_cmd = to_signed((m.dat[1] << 8) | m.dat[2], 16)
      elif m.address == 0x260 and m.src == 0:
        eps_torque = to_signed((m.dat[5] << 8) | m.dat[6], 16)
        steering_pressed = abs(to_signed((m.dat[1] << 8) | m.dat[2], 16)) > STEER_THRESHOLD

    if engaged and torque_cmd is not None and eps_torque is not None and not steering_pressed:
      cmds.append(torque_cmd)
      eps.append(eps_torque)
    else:
      if len(cmds) > MIN_SAMPLES:
        break
      cmds, eps = [], []

  if len(cmds) < MIN_SAMPLES:
    raise Exception("too few samples found in route")

  lm = linear_model.LinearRegression(fit_intercept=False)
  lm.fit(np.array(cmds).reshape(-1, 1), eps)
  scale_factor = 1. / lm.coef_[0]

  if plot:
    plt.plot(np.array(eps) * scale_factor)
    plt.plot(cmds)
    plt.show()
  return scale_factor