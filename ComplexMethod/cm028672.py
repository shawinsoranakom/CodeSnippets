def save(self,
           checkpoint_number: Optional[int] = None,
           check_interval: bool = True,
           options: Optional[tf.train.CheckpointOptions] = None):
    """See base class."""
    checkpoint_path = super().save(
        checkpoint_number=checkpoint_number,
        check_interval=check_interval,
        options=options)
    if not checkpoint_path:  # Nothing got written.
      return
    if not self._modules_to_export:  # No modules to export.
      logging.info('Skip saving SavedModel due to empty modules_to_export.')
      return checkpoint_path

    # Save the models for the checkpoint that just got written.
    saved_modules_directory = make_saved_modules_directory_name(checkpoint_path)
    # Atomic export of SavedModel. Write into a temporary direcotory and then
    # rename as the final direcotory after finishing the writing.
    # This can avoid trying to read an unfinished savedmodel.
    saved_modules_directory_tmp = saved_modules_directory + '_temp'
    for model_name, model in self._modules_to_export.items():
      signatures = getattr(model, 'saved_model_signatures', None)
      if signatures is not None:
        tf.saved_model.save(
            obj=model,
            export_dir=os.path.join(saved_modules_directory_tmp, model_name),
            signatures=signatures)
    if tf.io.gfile.exists(saved_modules_directory_tmp):
      tf.io.gfile.rename(saved_modules_directory_tmp, saved_modules_directory)

    saved_modules_directories_to_keep = [
        make_saved_modules_directory_name(ckpt) for ckpt in self.checkpoints
    ]
    existing_saved_modules_dirs = self.get_existing_savedmodels()

    self._savedmodels = []
    # Keep savedmodels in the same order as checkpoints (from oldest to newest).
    for saved_modules_dir_to_keep in saved_modules_directories_to_keep:
      if saved_modules_dir_to_keep in existing_saved_modules_dirs:
        self._savedmodels.append(saved_modules_dir_to_keep)

    for existing_saved_modules_dir in existing_saved_modules_dirs:
      if existing_saved_modules_dir not in self._savedmodels:
        tf.io.gfile.rmtree(existing_saved_modules_dir)

    return checkpoint_path