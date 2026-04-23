def _configure_embeddings(self):
        """Configure the Projector for embeddings."""
        from google.protobuf import text_format
        from tensorboard.plugins import projector

        config = projector.ProjectorConfig()
        for layer in self.model.layers:
            if isinstance(layer, Embedding):
                embedding = config.embeddings.add()
                # Embeddings are always the first layer, so this naming should
                # be consistent in any keras models checkpoints.
                name = (
                    "layer_with_weights-0/embeddings/.ATTRIBUTES/VARIABLE_VALUE"
                )
                embedding.tensor_name = name

                if self.embeddings_metadata is not None:
                    if isinstance(self.embeddings_metadata, str):
                        embedding.metadata_path = self.embeddings_metadata
                    else:
                        if layer.name in self.embeddings_metadata.keys():
                            embedding.metadata_path = (
                                self.embeddings_metadata.pop(layer.name)
                            )

        if self.embeddings_metadata and not isinstance(
            self.embeddings_metadata, str
        ):
            raise ValueError(
                "Unrecognized `Embedding` layer names passed to "
                "`keras.callbacks.TensorBoard` `embeddings_metadata` "
                f"argument: {self.embeddings_metadata.keys()}"
            )

        config_pbtxt = text_format.MessageToString(config)
        path = os.path.join(self._log_write_dir, "projector_config.pbtxt")
        with file_utils.File(path, "w") as f:
            f.write(config_pbtxt)