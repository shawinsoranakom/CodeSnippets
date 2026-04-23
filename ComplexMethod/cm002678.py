def from_pretrained(
        cls: type[SpecificPreTrainedConfigType],
        pretrained_model_name_or_path: str | os.PathLike,
        cache_dir: str | os.PathLike | None = None,
        force_download: bool = False,
        local_files_only: bool = False,
        token: str | bool | None = None,
        revision: str = "main",
        **kwargs,
    ) -> SpecificPreTrainedConfigType:
        r"""
        Instantiate a [`PreTrainedConfig`] (or a derived class) from a pretrained model configuration.

        Args:
            pretrained_model_name_or_path (`str` or `os.PathLike`):
                This can be either:

                - a string, the *model id* of a pretrained model configuration hosted inside a model repo on
                  huggingface.co.
                - a path to a *directory* containing a configuration file saved using the
                  [`~PreTrainedConfig.save_pretrained`] method, e.g., `./my_model_directory/`.
                - a path to a saved configuration JSON *file*, e.g., `./my_model_directory/configuration.json`.
            cache_dir (`str` or `os.PathLike`, *optional*):
                Path to a directory in which a downloaded pretrained model configuration should be cached if the
                standard cache should not be used.
            force_download (`bool`, *optional*, defaults to `False`):
                Whether or not to force to (re-)download the configuration files and override the cached versions if
                they exist.
            proxies (`dict[str, str]`, *optional*):
                A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
                'http://hostname': 'foo.bar:4012'}.` The proxies are used on each request.
            token (`str` or `bool`, *optional*):
                The token to use as HTTP bearer authorization for remote files. If `True`, or not specified, will use
                the token generated when running `hf auth login` (stored in `~/.huggingface`).
            revision (`str`, *optional*, defaults to `"main"`):
                The specific model version to use. It can be a branch name, a tag name, or a commit id, since we use a
                git-based system for storing models and other artifacts on huggingface.co, so `revision` can be any
                identifier allowed by git.

                <Tip>

                To test a pull request you made on the Hub, you can pass `revision="refs/pr/<pr_number>"`.

                </Tip>

            return_unused_kwargs (`bool`, *optional*, defaults to `False`):
                If `False`, then this function returns just the final configuration object.

                If `True`, then this functions returns a `Tuple(config, unused_kwargs)` where *unused_kwargs* is a
                dictionary consisting of the key/value pairs whose keys are not configuration attributes: i.e., the
                part of `kwargs` which has not been used to update `config` and is otherwise ignored.
            subfolder (`str`, *optional*, defaults to `""`):
                In case the relevant files are located inside a subfolder of the model repo on huggingface.co, you can
                specify the folder name here.
            kwargs (`dict[str, Any]`, *optional*):
                The values in kwargs of any keys which are configuration attributes will be used to override the loaded
                values. Behavior concerning key/value pairs whose keys are *not* configuration attributes is controlled
                by the `return_unused_kwargs` keyword parameter.

        Returns:
            [`PreTrainedConfig`]: The configuration object instantiated from this pretrained model.

        Examples:

        ```python
        # We can't instantiate directly the base class *PreTrainedConfig* so let's show the examples on a
        # derived class: BertConfig
        config = BertConfig.from_pretrained(
            "google-bert/bert-base-uncased"
        )  # Download configuration from huggingface.co and cache.
        config = BertConfig.from_pretrained(
            "./test/saved_model/"
        )  # E.g. config (or model) was saved using *save_pretrained('./test/saved_model/')*
        config = BertConfig.from_pretrained("./test/saved_model/my_configuration.json")
        config = BertConfig.from_pretrained("google-bert/bert-base-uncased", output_attentions=True, foo=False)
        assert config.output_attentions == True
        config, unused_kwargs = BertConfig.from_pretrained(
            "google-bert/bert-base-uncased", output_attentions=True, foo=False, return_unused_kwargs=True
        )
        assert config.output_attentions == True
        assert unused_kwargs == {"foo": False}
        ```"""
        kwargs["cache_dir"] = cache_dir
        kwargs["force_download"] = force_download
        kwargs["local_files_only"] = local_files_only
        kwargs["revision"] = revision

        config_dict, kwargs = cls.get_config_dict(pretrained_model_name_or_path, **kwargs)
        if cls.base_config_key and cls.base_config_key in config_dict:
            config_dict = config_dict[cls.base_config_key]

        if "model_type" in config_dict and hasattr(cls, "model_type") and config_dict["model_type"] != cls.model_type:
            # sometimes the config has no `base_config_key` if the config is used in several composite models
            # e.g. LlamaConfig. In that case we try to see if there is match in `model_type` before raising a warning
            for v in config_dict.values():
                if isinstance(v, dict) and v.get("model_type") == cls.model_type:
                    config_dict = v

            # raise warning only if we still can't see a match in `model_type`
            if config_dict["model_type"] != cls.model_type:
                logger.warning(
                    f"You are using a model of type `{config_dict['model_type']}` to instantiate a model of type "
                    f"`{cls.model_type}`. This may be expected if you are loading a checkpoint that shares a subset "
                    f"of the architecture (e.g., loading a `sam2_video` checkpoint into `Sam2Model`), but is otherwise "
                    f"not supported and can yield errors. Please verify that the checkpoint is compatible with the "
                    f"model you are instantiating."
                )

        return cls.from_dict(config_dict, **kwargs)