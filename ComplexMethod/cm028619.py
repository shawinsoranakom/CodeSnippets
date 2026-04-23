def initialize(self, model: tf_keras.Model):
    """Loading pretrained checkpoint."""
    if self._task_config.init_checkpoint_modules == 'backbone':
      raise ValueError(
          'init_checkpoint_modules=backbone is no longer supported. Specify'
          ' backbone checkpoints in each backbone config.'
      )

    if self._task_config.init_checkpoint_modules not in ['all', 'partial', '']:
      raise ValueError(
          'Unsupported init_checkpoint_modules: '
          f'{self._task_config.init_checkpoint_modules}'
      )

    if self._task_config.init_checkpoint and any(
        [b.init_checkpoint for b in self._task_config.model.backbones]
    ):
      raise ValueError(
          'A global init_checkpoint and a backbone init_checkpoint cannot be'
          ' specified at the same time.'
      )

    if self._task_config.init_checkpoint:
      global_ckpt_file = self._get_ckpt(self._task_config.init_checkpoint)
      ckpt = tf.train.Checkpoint(**model.checkpoint_items)
      status = ckpt.restore(global_ckpt_file).expect_partial()
      if self._task_config.init_checkpoint_modules != 'partial':
        status.assert_existing_objects_matched()
      logging.info(
          'Finished loading pretrained checkpoint from %s', global_ckpt_file
      )
    else:
      # This case means that no global checkpoint was provided. Possibly,
      # backbone-specific checkpoints were.
      for backbone_config, backbone in zip(
          self._task_config.model.backbones, model.backbones
      ):
        if not backbone_config.init_checkpoint:
          continue

        backbone_init_ckpt = self._get_ckpt(backbone_config.init_checkpoint)
        if backbone_config.backbone.type == 'uvit':
          # The UVit object has a special function called load_checkpoint.
          # The other backbones do not.
          backbone.load_checkpoint(ckpt_filepath=backbone_init_ckpt)
        else:
          ckpt = tf.train.Checkpoint(backbone=backbone)
          status = (
              ckpt.restore(backbone_init_ckpt)
              .expect_partial()
              .assert_nontrivial_match()
          )
          if backbone_config.assert_existing_objects_matched:
            status.assert_existing_objects_matched()

        logging.info(
            'Finished loading pretrained backbone from %s', backbone_init_ckpt
        )