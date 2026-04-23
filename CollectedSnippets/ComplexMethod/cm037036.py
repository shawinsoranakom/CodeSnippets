def _set_default_parameters(self, model_config: ModelConfig):
        if self.task in ["embed", "token_embed"]:
            if self.use_activation is None:
                self.use_activation = True

            if self.dimensions is not None:
                if not model_config.is_matryoshka:
                    raise ValueError(
                        f'Model "{model_config.served_model_name}" does not '
                        f"support matryoshka representation, "
                        f"changing output dimensions will lead to poor results."
                    )

                mds = model_config.matryoshka_dimensions
                if mds is not None:
                    if self.dimensions not in mds:
                        raise ValueError(
                            f"Model {model_config.served_model_name!r} "
                            f"only supports {str(mds)} matryoshka dimensions, "
                            f"use other output dimensions will "
                            f"lead to poor results."
                        )
                elif self.dimensions < 1:
                    raise ValueError("Dimensions must be greater than 0")

        elif self.task in ["classify", "token_classify"]:
            if self.use_activation is None:
                self.use_activation = True
        else:
            raise ValueError(f"Unknown pooling task: {self.task!r}")