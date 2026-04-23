def _build_struct(self, net, inputs):
    if self._use_reorg_input:
      inputs = nn_blocks.Reorg()(inputs)
      net[0].filters = net[1].filters
      net[0].output_name = net[1].output_name
      del net[1]

    endpoints = collections.OrderedDict()
    stack_outputs = [inputs]
    for i, config in enumerate(net):
      if config.output_name > self._max_size:
        break
      if config.output_name in self._csp_level_mod:
        config.stack = 'residual'

      config.filters = int(config.filters * self._width_scale)
      config.repetitions = int(config.repetitions * self._depth_scale)

      if config.stack is None:
        x = self._build_block(
            stack_outputs[config.route], config, name=f'{config.layer}_{i}')
        stack_outputs.append(x)
      elif config.stack == 'residual':
        x = self._residual_stack(
            stack_outputs[config.route], config, name=f'{config.layer}_{i}')
        stack_outputs.append(x)
      elif config.stack == 'csp':
        x = self._csp_stack(
            stack_outputs[config.route], config, name=f'{config.layer}_{i}')
        stack_outputs.append(x)
      elif config.stack == 'csp_tiny':
        x_pass, x = self._csp_tiny_stack(
            stack_outputs[config.route], config, name=f'{config.layer}_{i}')
        stack_outputs.append(x_pass)
      elif config.stack == 'tiny':
        x = self._tiny_stack(
            stack_outputs[config.route], config, name=f'{config.layer}_{i}')
        stack_outputs.append(x)
      if (config.is_output and self._min_size is None):
        endpoints[str(config.output_name)] = x
      elif (self._min_size is not None and
            config.output_name >= self._min_size and
            config.output_name <= self._max_size):
        endpoints[str(config.output_name)] = x

    self._output_specs = {l: endpoints[l].get_shape() for l in endpoints.keys()}
    return endpoints