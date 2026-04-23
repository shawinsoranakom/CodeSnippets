def _replicated_step(inputs, mem=None):
      """Replicated training step."""

      inputs["mems"] = mem
      with tf.GradientTape() as tape:
        mem, logits = model(inputs, training=True)
        loss = model.losses
        train_loss_metric.update_state(loss)
        if train_metric:
          train_metric.update_state(inputs["label_ids"], logits)
        scaled_loss = loss[0] * 1.0 / float(strategy.num_replicas_in_sync)

      # Collects training variables.
      tvars = model.trainable_variables
      grads = tape.gradient(scaled_loss, tvars)
      clipped, _ = tf.clip_by_global_norm(grads, clip_norm=1.0)

      if input_meta_data["lr_layer_decay_rate"] != 1.0:
        n_layer = 0
        for i in range(len(clipped)):
          m = re.search(r"model/transformer/layer_(\d+?)/", tvars[i].name)
          if not m:
            continue
          n_layer = max(n_layer, int(m.group(1)) + 1)

        for i in range(len(clipped)):
          for l in range(n_layer):
            if "model/transformer/layer_{}/".format(l) in tvars[i].name:
              abs_rate = input_meta_data["lr_layer_decay_rate"]**(
                  n_layer - 1 - l)
              clipped[i] *= abs_rate
              logging.info("Apply mult {:.4f} to layer-{} grad of {}".format(
                  abs_rate, l, tvars[i].name))
              break

      optimizer.apply_gradients(zip(clipped, tvars))
      if input_meta_data["mem_len"] > 0:
        return mem