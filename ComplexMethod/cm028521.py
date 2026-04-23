def activation_fn(features: tf.Tensor, act_fn: str):
  """Customized non-linear activation type."""
  if act_fn in ('silu', 'swish'):
    return tf.nn.swish(features)
  elif act_fn == 'silu_native':
    return features * tf.sigmoid(features)
  elif act_fn == 'hswish':
    return features * tf.nn.relu6(features + 3) / 6
  elif act_fn == 'relu':
    return tf.nn.relu(features)
  elif act_fn == 'relu6':
    return tf.nn.relu6(features)
  elif act_fn == 'elu':
    return tf.nn.elu(features)
  elif act_fn == 'leaky_relu':
    return tf.nn.leaky_relu(features)
  elif act_fn == 'selu':
    return tf.nn.selu(features)
  elif act_fn == 'mish':
    return features * tf.math.tanh(tf.math.softplus(features))
  elif act_fn == 'gelu':
    return (
        0.5
        * features
        * (
            1
            + tf.tanh(
                np.sqrt(2 / np.pi) * (features + 0.044715 * tf.pow(features, 3))
            )
        )
    )
  else:
    raise ValueError('Unsupported act_fn {}'.format(act_fn))