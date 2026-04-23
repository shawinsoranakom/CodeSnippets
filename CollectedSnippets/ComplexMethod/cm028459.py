def get_callbacks(
    model_checkpoint: bool = True,
    include_tensorboard: bool = True,
    time_history: bool = True,
    track_lr: bool = True,
    write_model_weights: bool = True,
    apply_moving_average: bool = False,
    initial_step: int = 0,
    batch_size: int = 0,
    log_steps: int = 0,
    model_dir: Optional[str] = None,
    backup_and_restore: bool = False) -> List[tf_keras.callbacks.Callback]:
  """Get all callbacks."""
  model_dir = model_dir or ''
  callbacks = []
  if model_checkpoint:
    ckpt_full_path = os.path.join(model_dir, 'model.ckpt-{epoch:04d}')
    callbacks.append(
        tf_keras.callbacks.ModelCheckpoint(
            ckpt_full_path, save_weights_only=True, verbose=1))
  if backup_and_restore:
    backup_dir = os.path.join(model_dir, 'tmp')
    callbacks.append(
        tf_keras.callbacks.experimental.BackupAndRestore(backup_dir))
  if include_tensorboard:
    callbacks.append(
        CustomTensorBoard(
            log_dir=model_dir,
            track_lr=track_lr,
            initial_step=initial_step,
            write_images=write_model_weights,
            profile_batch=0))
  if time_history:
    callbacks.append(
        keras_utils.TimeHistory(
            batch_size,
            log_steps,
            logdir=model_dir if include_tensorboard else None))
  if apply_moving_average:
    # Save moving average model to a different file so that
    # we can resume training from a checkpoint
    ckpt_full_path = os.path.join(model_dir, 'average',
                                  'model.ckpt-{epoch:04d}')
    callbacks.append(
        AverageModelCheckpoint(
            update_weights=False,
            filepath=ckpt_full_path,
            save_weights_only=True,
            verbose=1))
    callbacks.append(MovingAverageCallback())
  return callbacks