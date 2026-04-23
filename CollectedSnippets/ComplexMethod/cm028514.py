def _resource_apply_dense(self, grad, var, apply_state=None):
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

      m = self.get_slot(var, 'm')
      v = self.get_slot(var, 'v')
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
        return tf.raw_ops.ResourceApplyAdam(
            var=var.handle,
            m=m.handle,
            v=v.handle,
            beta1_power=coefficients['beta_1_power'],
            beta2_power=coefficients['beta_2_power'],
            lr=lr,
            beta1=coefficients['beta_1_t'],
            beta2=coefficients['beta_2_t'],
            epsilon=coefficients['epsilon'],
            grad=grad,
            use_locking=self._use_locking)
      else:
        vhat = self.get_slot(var, 'vhat')
        return tf.raw_ops.ResourceApplyAdamWithAmsgrad(
            var=var.handle,
            m=m.handle,
            v=v.handle,
            vhat=vhat.handle,
            beta1_power=coefficients['beta_1_power'],
            beta2_power=coefficients['beta_2_power'],
            lr=lr,
            beta1=coefficients['beta_1_t'],
            beta2=coefficients['beta_2_t'],
            epsilon=coefficients['epsilon'],
            grad=grad,
            use_locking=self._use_locking)