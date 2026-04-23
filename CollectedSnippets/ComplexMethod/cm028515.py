def _resource_apply_sparse(self, grad, var, indices, apply_state=None):
    lr_t, kwargs = self._get_lr(var.device, var.dtype.base_dtype, apply_state)
    apply_state = kwargs['apply_state']
    if (
        self._layer_decay != 1.0
        and self._vars_substr is not None
        and self._layers_idx is not None
    ):
      is_decayed = False
      for var_substr, idx in zip(self._vars_substr, self._layers_idx):
        if var_substr in var.name:
          decay_factor = self._layer_decay ** (self._max_idx - idx)
          lr_t = lr_t * decay_factor
          is_decayed = True
          logging.debug(
              'Applying layer-wise lr decay: %s: %f', var.name, decay_factor)
          break
      if not is_decayed:
        logging.debug('Ignore layer-wise lr decay: %s', var.name)
    decay = self._decay_weights_op(var, lr_t, apply_state)
    with tf.control_dependencies([decay]):
      var_device, var_dtype = var.device, var.dtype.base_dtype
      coefficients = ((apply_state or {}).get((var_device, var_dtype))
                      or self._fallback_apply_state(var_device, var_dtype))

      # m_t = beta1 * m + (1 - beta1) * g_t
      m = self.get_slot(var, 'm')
      m_scaled_g_values = grad * coefficients['one_minus_beta_1_t']
      m_t = tf.compat.v1.assign(m, m * coefficients['beta_1_t'],
                                use_locking=self._use_locking)
      with tf.control_dependencies([m_t]):
        m_t = self._resource_scatter_add(m, indices, m_scaled_g_values)

      # v_t = beta2 * v + (1 - beta2) * (g_t * g_t)
      v = self.get_slot(var, 'v')
      v_scaled_g_values = (grad * grad) * coefficients['one_minus_beta_2_t']
      v_t = tf.compat.v1.assign(v, v * coefficients['beta_2_t'],
                                use_locking=self._use_locking)
      with tf.control_dependencies([v_t]):
        v_t = self._resource_scatter_add(v, indices, v_scaled_g_values)
      lr = coefficients['lr_t']
      if (
          self._layer_decay != 1.0
          and self._vars_substr is not None
          and self._layers_idx is not None
      ):
        for var_substr, idx in zip(self._vars_substr, self._layers_idx):
          if var_substr in var.name:
            lr = lr * (self._layer_decay ** (self._max_idx - idx))
            break
      if not self.amsgrad:
        v_sqrt = tf.sqrt(v_t)
        var_update = tf.compat.v1.assign_sub(
            var, lr * m_t / (v_sqrt + coefficients['epsilon']),
            use_locking=self._use_locking)
        return tf.group(*[var_update, m_t, v_t])
      else:
        v_hat = self.get_slot(var, 'vhat')
        v_hat_t = tf.maximum(v_hat, v_t)
        with tf.control_dependencies([v_hat_t]):
          v_hat_t = tf.compat.v1.assign(
              v_hat, v_hat_t, use_locking=self._use_locking)
        v_hat_sqrt = tf.sqrt(v_hat_t)
        var_update = tf.compat.v1.assign_sub(
            var,
            lr* m_t / (v_hat_sqrt + coefficients['epsilon']),
            use_locking=self._use_locking)
        return tf.group(*[var_update, m_t, v_t, v_hat_t])