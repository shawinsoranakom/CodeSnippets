def _qrnn_preprocess(self, gates):
    """Preprocess the gate inputs to the pooling layer."""
    assert self.num_gates == len(gates)
    dim = lambda tensor, index: tensor.get_shape().as_list()[index]

    for tensor in gates:
      assert len(tensor.get_shape().as_list()) == 3
      for idx in range(3):
        assert dim(gates[0], idx) == dim(tensor, idx)

    if self.pooling == QUASI_RNN_POOLING_F:
      z = self.quantized_tanh(gates[0], tf_only=True)
      f = self.quantized_sigmoid(gates[1], tf_only=True)
      return f, self.qrange_tanh(self.qrange_sigmoid(1 - f) * z), 1
    elif self.pooling == QUASI_RNN_POOLING_FO:
      z = self.quantized_tanh(gates[0], tf_only=True)
      f = self.quantized_sigmoid(gates[1], tf_only=True)
      o = self.quantized_sigmoid(gates[2], tf_only=True)
      return f, self.qrange_tanh(self.qrange_sigmoid(1 - f) * z), o
    else:  # self.pooling == QUASI_RNN_POOLING_IFO:
      z = self.quantized_tanh(gates[0], tf_only=True)
      i = self.quantized_sigmoid(gates[1], tf_only=True)
      f = self.quantized_sigmoid(gates[2], tf_only=True)
      o = self.quantized_sigmoid(gates[3], tf_only=True)
      return f, self.qrange_tanh(i * z), o