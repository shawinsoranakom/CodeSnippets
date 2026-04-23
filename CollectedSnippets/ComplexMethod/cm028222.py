def _verify_config(self, inputs):
    """Verify that MnasFPN config and its inputs."""
    num_inputs = len(inputs)
    assert len(self._head_def['feature_levels']) == num_inputs

    base_width = inputs[0].shape.as_list(
    )[1] * 2**self._head_def['feature_levels'][0]
    for i in range(1, num_inputs):
      width = inputs[i].shape.as_list()[1]
      level = self._head_def['feature_levels'][i]
      expected_width = base_width // 2**level
      if width != expected_width:
        raise ValueError(
            'Resolution of input {} does not match its level {}.'.format(
                i, level))

    for cell_spec in self._head_def['spec']:
      # The last K nodes in a cell are the inputs to the next cell. Assert that
      # their feature maps are at the right level.
      for i in range(num_inputs):
        if cell_spec[-num_inputs +
                     i].output_level != self._head_def['feature_levels'][i]:
          raise ValueError(
              'Mismatch between node level {} and desired output level {}.'
              .format(cell_spec[-num_inputs + i].output_level,
                      self._head_def['feature_levels'][i]))
      # Assert that each block only uses precending blocks.
      for bi, block_spec in enumerate(cell_spec):
        for inp in block_spec.inputs:
          if inp >= bi + num_inputs:
            raise ValueError(
                'Block {} is trying to access uncreated block {}.'.format(
                    bi, inp))