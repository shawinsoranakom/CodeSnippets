def _process_deprecations(self, layer: dict[str, T.Any]) -> None:  # noqa[C901]
        """Some layer kwargs are deprecated between Keras 2 and Keras 3. Some are not mission
        critical, but updating these here prevents Keras from outputting warnings about deprecated
        arguments. Others will fail to load the legacy model (eg Clip) so are replaced with a new
        config. Operation is performed in place

        Parameters
        ----------
        layer
            A keras model config item representing a keras layer
        """
        if layer["class_name"] == "LeakyReLU":
            # Non mission-critical, but prevents scary deprecation messages
            config = layer["config"]
            old, new = "alpha", "negative_slope"
            if old in config:
                logger.debug("Updating '%s' kwarg '%s' to '%s'", layer["name"], old, new)
                config[new] = config[old]
                del config[old]

        if layer["name"] == "visual":
            # MultiHeadAttention is not backwards compatible, so get new config for Clip models
            logger.debug("Getting new config for 'visual' model")
            layer["config"] = self._get_clip_config()

        if layer["class_name"] == "TFOpLambda":
            # TFLambdaOp are not supported
            self._convert_lambda_config(layer)

        if layer["class_name"] in ("DepthwiseConv2D",
                                   "SeparableConv2D",
                                   "Conv2DTranspose") and "groups" in layer["config"]:
            # groups parameter doesn't exist in Keras 3. Hopefully it still works the same
            logger.debug("Removing groups from %s '%s'", layer["class_name"], layer["name"])
            del layer["config"]["groups"]

        if layer["class_name"] == "SeparableConv2D":
            for key in ("kernel_initializer", "kernel_regularizer", "kernel_constraint"):
                logger.debug("Removing '%s' from %s '%s'", key, layer["class_name"], layer["name"])
                del layer["config"][key]

        if "dtype" in layer["config"]:
            # Incorrectly stored dtypes error when deserializing the new config. May be a Keras bug
            actual_dtype = None
            old_dtype = layer["config"]["dtype"]
            if isinstance(old_dtype, str):
                actual_dtype = layer["config"]["dtype"]
            if isinstance(old_dtype, dict) and old_dtype.get("class_name") == "Policy":
                actual_dtype = old_dtype["config"]["name"]

            if actual_dtype is not None:
                new_dtype = {"module": "keras",
                             "class_name": "DTypePolicy",
                             "config": {"name": actual_dtype},
                             "registered_name": None}
                logger.debug("Updating dtype for '%s' from %s to %s", layer["name"],
                             old_dtype, new_dtype)
                layer["config"]["dtype"] = new_dtype