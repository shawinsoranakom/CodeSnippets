def build_losses(self, labels, outputs, metrics) -> tf.Tensor:
    """Builds losses and update loss-related metrics for the current stage."""
    last_stage = 'student_pretrainer_output' in outputs

    # Layer-wise warmup stage
    if not last_stage:
      distill_config = self._progressive_config.layer_wise_distill_config
      teacher_feature = outputs['teacher_output_feature']
      student_feature = outputs['student_output_feature']

      feature_transfer_loss = tf_keras.losses.mean_squared_error(
          self._layer_norm(teacher_feature), self._layer_norm(student_feature))
      feature_transfer_loss *= distill_config.hidden_distill_factor
      beta_loss, gamma_loss = self._get_distribution_losses(teacher_feature,
                                                            student_feature)
      beta_loss *= distill_config.beta_distill_factor
      gamma_loss *= distill_config.gamma_distill_factor
      total_loss = feature_transfer_loss + beta_loss + gamma_loss

      if distill_config.if_transfer_attention:
        teacher_attention = outputs['teacher_attention_score']
        student_attention = outputs['student_attention_score']
        attention_loss = self._get_attention_loss(teacher_attention,
                                                  student_attention)
        attention_loss *= distill_config.attention_distill_factor
        total_loss += attention_loss

      total_loss /= tf.cast((self._stage_id + 1), tf.float32)

    # Last stage to distill pretraining layer.
    else:
      distill_config = self._progressive_config.pretrain_distill_config
      lm_label = labels['masked_lm_ids']
      vocab_size = (
          self._task_config.student_model.encoder.mobilebert.word_vocab_size)

      # Shape: [batch, max_predictions_per_seq, vocab_size]
      lm_label = tf.one_hot(indices=lm_label, depth=vocab_size, on_value=1.0,
                            off_value=0.0, axis=-1, dtype=tf.float32)
      gt_ratio = distill_config.distill_ground_truth_ratio
      if gt_ratio != 1.0:
        teacher_mlm_logits = outputs['teacher_pretrainer_output']['mlm_logits']
        teacher_labels = tf.nn.softmax(teacher_mlm_logits, axis=-1)
        lm_label = gt_ratio * lm_label + (1-gt_ratio) * teacher_labels

      student_pretrainer_output = outputs['student_pretrainer_output']
      # Shape: [batch, max_predictions_per_seq, vocab_size]
      student_lm_log_probs = tf.nn.log_softmax(
          student_pretrainer_output['mlm_logits'], axis=-1)

      # Shape: [batch * max_predictions_per_seq]
      per_example_loss = tf.reshape(
          -tf.reduce_sum(student_lm_log_probs * lm_label, axis=[-1]), [-1])

      lm_label_weights = tf.reshape(labels['masked_lm_weights'], [-1])
      lm_numerator_loss = tf.reduce_sum(per_example_loss * lm_label_weights)
      lm_denominator_loss = tf.reduce_sum(lm_label_weights)
      mlm_loss = tf.math.divide_no_nan(lm_numerator_loss, lm_denominator_loss)
      total_loss = mlm_loss

      if 'next_sentence_labels' in labels:
        sentence_labels = labels['next_sentence_labels']
        sentence_outputs = tf.cast(
            student_pretrainer_output['next_sentence'], dtype=tf.float32)
        sentence_loss = tf.reduce_mean(
            tf_keras.losses.sparse_categorical_crossentropy(
                sentence_labels, sentence_outputs, from_logits=True))
        total_loss += sentence_loss

    # Also update loss-related metrics here, instead of in `process_metrics`.
    metrics = dict([(metric.name, metric) for metric in metrics])

    if not last_stage:
      metrics['feature_transfer_mse'].update_state(feature_transfer_loss)
      metrics['beta_transfer_loss'].update_state(beta_loss)
      metrics['gamma_transfer_loss'].update_state(gamma_loss)
      layer_wise_config = self._progressive_config.layer_wise_distill_config
      if layer_wise_config.if_transfer_attention:
        metrics['attention_transfer_loss'].update_state(attention_loss)
    else:
      metrics['lm_example_loss'].update_state(mlm_loss)
      if 'next_sentence_labels' in labels:
        metrics['next_sentence_loss'].update_state(sentence_loss)
    metrics['total_loss'].update_state(total_loss)

    return total_loss