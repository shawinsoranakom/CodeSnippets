def _customized_vmae_initialize(self,
                                  model: tf_keras.Model,
                                  ckpt_dir_or_file: str):
    """Loads pretrained Video MAE checkpoint."""
    with tf.io.gfile.GFile(ckpt_dir_or_file, 'rb') as ckpt:
      weights = np.load(ckpt, allow_pickle=True)

    ckpt_names = list(weights[()].keys())
    ckpt_names = [n for n in ckpt_names if 'pred_head' not in n]

    skipped = []
    loaded = []
    for krs_w in model.weights:
      krs_name = krs_w.name
      # Handle the first block naming.
      krs_name = krs_name.replace('encoder/transformer_encoder_block/',
                                  'encoder/transformer_encoder_block_0/')
      ckpt_name = self._remap_variable_name(krs_name, _VMAE_CKPT_MAPPING)
      if ckpt_name in ckpt_names:
        ckpt_weight = weights[()][ckpt_name]
        ckpt_weight = self._maybe_transpose_pytorch_weight(ckpt_weight)

        if ckpt_weight.shape == krs_w.shape:
          krs_w.assign(ckpt_weight)
          loaded.append(ckpt_name)
        elif 'kernel' in krs_name and any(
            [keyword in krs_name for keyword in ['key', 'query', 'value']]):
          cin, cout = ckpt_weight.shape
          num_heads = krs_w.shape[1]
          ckpt_weight = tf.reshape(
              ckpt_weight, [cin, num_heads, cout // num_heads])
          krs_w.assign(ckpt_weight)
          loaded.append(ckpt_name)
        elif 'bias' in krs_name and any(
            [keyword in krs_name for keyword in ['key', 'query', 'value']]):
          cout = ckpt_weight.shape[0]
          num_heads = krs_w.shape[0]
          ckpt_weight = tf.reshape(ckpt_weight, [num_heads, cout // num_heads])
          krs_w.assign(ckpt_weight)
          loaded.append(ckpt_name)
        elif 'kernel' in krs_name and 'attention_output' in krs_name:
          cin, cout = ckpt_weight.shape
          num_heads = krs_w.shape[0]
          ckpt_weight = tf.reshape(ckpt_weight,
                                   [num_heads, cin // num_heads, cout])
          krs_w.assign(ckpt_weight)
          loaded.append(ckpt_name)
        else:
          skipped.append(krs_name)
      else:
        skipped.append(krs_name)

    leftover = set(ckpt_names) - set(loaded)
    logging.info('skipped: %s', skipped)
    logging.info('leftover: %s', leftover)

    if any([('encoder' in v or 'conv3d' in v or 'pos_embedding' in v)
            for v in skipped]):
      raise ValueError('ViT backbone is only partially loaded.')
    logging.info('Finished loading pretrained checkpoint from %s',
                 ckpt_dir_or_file)