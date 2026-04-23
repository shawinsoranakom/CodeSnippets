def _save_model(self, epoch, batch, logs):
        """Saves the model.

        Args:
            epoch: the epoch this iteration is in.
            batch: the batch this iteration is in. `None` if the `save_freq`
                is set to `"epoch"`.
            logs: the `logs` dict passed in to `on_batch_end` or `on_epoch_end`.
        """
        filepath = self._get_file_path(epoch, batch, logs)

        try:
            if self._should_save_model(epoch, batch, logs, filepath):
                # Create host directory if it doesn't exist.
                dirname = os.path.dirname(filepath)
                if dirname and not file_utils.exists(dirname):
                    file_utils.makedirs(dirname)

                if self.save_weights_only:
                    self.model.save_weights(filepath, overwrite=True)
                else:
                    self.model.save(filepath, overwrite=True)
                if self.verbose > 0:
                    io_utils.print_msg(
                        f"\nEpoch {epoch + 1}: "
                        f"finished saving model to {filepath}"
                    )
        except IsADirectoryError:  # h5py 3.x
            raise IOError(
                "Please specify a non-directory filepath for "
                "ModelCheckpoint. Filepath used is an existing "
                f"directory: {filepath}"
            )
        except IOError as e:  # h5py 2.x
            # `e.errno` appears to be `None` so checking the content of
            # `e.args[0]`.
            if "is a directory" in str(e.args[0]).lower():
                raise IOError(
                    "Please specify a non-directory filepath for "
                    "ModelCheckpoint. Filepath used is an existing "
                    f"directory: f{filepath}"
                )
            # Re-throw the error for any other causes.
            raise e