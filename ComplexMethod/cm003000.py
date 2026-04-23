def from_vision_text_pretrained(
        cls,
        vision_model_name_or_path: str | None = None,
        text_model_name_or_path: str | None = None,
        *model_args,
        **kwargs,
    ) -> PreTrainedModel:
        """
        Params:
            vision_model_name_or_path (`str`, *optional*, defaults to `None`):
                Information necessary to initiate the vision model. Can be either:

                    - A string, the *model id* of a pretrained model hosted inside a model repo on huggingface.co.
                    - A path to a *directory* containing model weights saved using
                      [`~PreTrainedModel.save_pretrained`], e.g., `./my_model_directory/`.
                    - a path to a *PyTorch checkpoint folder* (e.g, `./pt_model`). In this case, a configuration
                      object should be provided as `config` argument.

            text_model_name_or_path (`str`, *optional*):
                Information necessary to initiate the text model. Can be either:

                    - A string, the *model id* of a pretrained model hosted inside a model repo on huggingface.co.
                    - A path to a *directory* containing model weights saved using
                      [`~PreTrainedModel.save_pretrained`], e.g., `./my_model_directory/`.
                    - a path to a *PyTorch checkpoint folder* (e.g, `./pt_model`). In this case, a configuration
                      object should be provided as `config` argument.

            model_args (remaining positional arguments, *optional*):
                All remaining positional arguments will be passed to the underlying model's `__init__` method.

            kwargs (remaining dictionary of keyword arguments, *optional*):
                Can be used to update the configuration object (after it being loaded) and initiate the model (e.g.,
                `output_attentions=True`).

                - To update the text configuration, use the prefix *text_* for each configuration parameter.
                - To update the vision configuration, use the prefix *vision_* for each configuration parameter.
                - To update the parent model configuration, do not use a prefix for each configuration parameter.

                Behaves differently depending on whether a `config` is provided or automatically loaded.

        Example:

        ```python
        >>> from transformers import VisionTextDualEncoderModel

        >>> # initialize a model from pretrained ViT and BERT models. Note that the projection layers will be randomly initialized.
        >>> model = VisionTextDualEncoderModel.from_vision_text_pretrained(
        ...     "google/vit-base-patch16-224", "google-bert/bert-base-uncased"
        ... )
        >>> # saving model after fine-tuning
        >>> model.save_pretrained("./vit-bert")
        >>> # load fine-tuned model
        >>> model = VisionTextDualEncoderModel.from_pretrained("./vit-bert")
        ```"""
        kwargs_vision = {
            argument[len("vision_") :]: value for argument, value in kwargs.items() if argument.startswith("vision_")
        }

        kwargs_text = {
            argument[len("text_") :]: value for argument, value in kwargs.items() if argument.startswith("text_")
        }

        # remove vision, text kwargs from kwargs
        for key in kwargs_vision:
            del kwargs["vision_" + key]
        for key in kwargs_text:
            del kwargs["text_" + key]

        # Load and initialize the vision and text model
        vision_model = kwargs_vision.pop("model", None)
        if vision_model is None:
            if vision_model_name_or_path is None:
                raise ValueError(
                    "If `vision_model` is not defined as an argument, a `vision_model_name_or_path` has to be defined"
                )

            if "config" not in kwargs_vision:
                vision_config = AutoConfig.from_pretrained(vision_model_name_or_path)

            if vision_config.model_type == "clip":
                kwargs_vision["config"] = vision_config.vision_config
                vision_model = CLIPVisionModel.from_pretrained(vision_model_name_or_path, *model_args, **kwargs_vision)
                # TODO: Should we use the pre-trained projection as well ?
            else:
                kwargs_vision["config"] = vision_config
                vision_model = AutoModel.from_pretrained(vision_model_name_or_path, *model_args, **kwargs_vision)

        text_model = kwargs_text.pop("model", None)
        if text_model is None:
            if text_model_name_or_path is None:
                raise ValueError(
                    "If `text_model` is not defined as an argument, a `text_model_name_or_path` has to be defined"
                )

            if "config" not in kwargs_text:
                text_config = AutoConfig.from_pretrained(text_model_name_or_path)
                kwargs_text["config"] = text_config

            text_model = AutoModel.from_pretrained(text_model_name_or_path, *model_args, **kwargs_text)

        # instantiate config with corresponding kwargs
        config = VisionTextDualEncoderConfig.from_vision_text_configs(vision_model.config, text_model.config, **kwargs)

        # init model
        model = cls(config=config, vision_model=vision_model, text_model=text_model)

        # the projection layers are always newly initialized when loading the model
        # using pre-trained vision and text model.
        logger.warning(
            "The projection layer and logit scale weights `['visual_projection.weight', 'text_projection.weight',"
            " 'logit_scale']` are newly initialized. You should probably TRAIN this model on a down-stream task to be"
            " able to use it for predictions and inference."
        )

        return model