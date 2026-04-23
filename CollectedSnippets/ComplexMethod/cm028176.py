def virtual_adversarial_loss_bidir(logits, embedded, inputs,
                                   logits_from_embedding_fn):
  """Virtual adversarial loss for bidirectional models."""
  logits = tf.stop_gradient(logits)
  f_inputs, _ = inputs
  weights = f_inputs.eos_weights
  if FLAGS.single_label:
    indices = tf.stack([tf.range(FLAGS.batch_size), f_inputs.length - 1], 1)
    weights = tf.expand_dims(tf.gather_nd(f_inputs.eos_weights, indices), 1)
  assert weights is not None

  perturbs = [
      _mask_by_length(tf.random_normal(shape=tf.shape(emb)), f_inputs.length)
      for emb in embedded
  ]
  for _ in xrange(FLAGS.num_power_iteration):
    perturbs = [
        _scale_l2(d, FLAGS.small_constant_for_finite_diff) for d in perturbs
    ]
    d_logits = logits_from_embedding_fn(
        [emb + d for (emb, d) in zip(embedded, perturbs)])
    kl = _kl_divergence_with_logits(logits, d_logits, weights)
    perturbs = tf.gradients(
        kl,
        perturbs,
        aggregation_method=tf.AggregationMethod.EXPERIMENTAL_ACCUMULATE_N)
    perturbs = [tf.stop_gradient(d) for d in perturbs]

  perturbs = [_scale_l2(d, FLAGS.perturb_norm_length) for d in perturbs]
  vadv_logits = logits_from_embedding_fn(
      [emb + d for (emb, d) in zip(embedded, perturbs)])
  return _kl_divergence_with_logits(logits, vadv_logits, weights)