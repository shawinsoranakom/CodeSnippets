def initialize(self, model: tf_keras.Model) -> None:
    """Loads pretrained checkpoint."""

    if not self.task_config.init_checkpoint:
      return

    def _get_checkpoint_path(checkpoint_dir_or_file):
      checkpoint_path = checkpoint_dir_or_file
      if tf.io.gfile.isdir(checkpoint_dir_or_file):
        checkpoint_path = tf.train.latest_checkpoint(
            checkpoint_dir_or_file)
      return checkpoint_path

    for init_module in self.task_config.init_checkpoint_modules:
      # Restoring checkpoint.
      if init_module == 'all':
        checkpoint_path = _get_checkpoint_path(
            self.task_config.init_checkpoint)
        ckpt = tf.train.Checkpoint(**model.checkpoint_items)
        status = ckpt.read(checkpoint_path)
        status.expect_partial().assert_existing_objects_matched()

      elif init_module == 'backbone':
        checkpoint_path = _get_checkpoint_path(
            self.task_config.init_checkpoint)

        if self.task_config.model.backbone.type == 'uvit':
          model.backbone.load_checkpoint(ckpt_filepath=checkpoint_path)
        else:
          ckpt = tf.train.Checkpoint(backbone=model.backbone)
          status = ckpt.read(checkpoint_path)
          status.expect_partial().assert_existing_objects_matched()

      elif init_module == 'decoder':
        checkpoint_path = _get_checkpoint_path(
            self.task_config.init_checkpoint)
        ckpt = tf.train.Checkpoint(decoder=model.decoder)
        status = ckpt.read(checkpoint_path)
        status.expect_partial().assert_existing_objects_matched()

      elif init_module == 'segmentation_backbone':
        checkpoint_path = _get_checkpoint_path(
            self.task_config.segmentation_init_checkpoint)
        ckpt = tf.train.Checkpoint(
            segmentation_backbone=model.segmentation_backbone)
        status = ckpt.read(checkpoint_path)
        status.expect_partial().assert_existing_objects_matched()

      elif init_module == 'segmentation_decoder':
        checkpoint_path = _get_checkpoint_path(
            self.task_config.segmentation_init_checkpoint)
        ckpt = tf.train.Checkpoint(
            segmentation_decoder=model.segmentation_decoder)
        status = ckpt.read(checkpoint_path)
        status.expect_partial().assert_existing_objects_matched()

      else:
        raise ValueError(
            "Only 'all', 'backbone', 'decoder', 'segmentation_backbone' and/or "
            "'segmentation_decoder' can be used to initialize the model, but "
            "got {}".format(init_module))
      logging.info('Finished loading pretrained checkpoint from %s for %s',
                   checkpoint_path, init_module)