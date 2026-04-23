def __init__(
        self,
        filepath,
        call_endpoint="serve",
        call_training_endpoint=None,
        trainable=True,
        name=None,
        dtype=None,
    ):
        if backend.backend() != "tensorflow":
            raise NotImplementedError(
                "The TFSMLayer is only currently supported with the "
                "TensorFlow backend."
            )

        # Initialize an empty layer, then add_weight() etc. as needed.
        super().__init__(trainable=trainable, name=name, dtype=dtype)

        self._reloaded_obj = tf.saved_model.load(filepath)

        self.filepath = filepath
        self.call_endpoint = call_endpoint
        self.call_training_endpoint = call_training_endpoint

        # Resolve the call function.
        if hasattr(self._reloaded_obj, call_endpoint):
            # Case 1: it's set as an attribute.
            self.call_endpoint_fn = getattr(self._reloaded_obj, call_endpoint)
        elif call_endpoint in self._reloaded_obj.signatures:
            # Case 2: it's listed in the `signatures` field.
            self.call_endpoint_fn = self._reloaded_obj.signatures[call_endpoint]
        else:
            raise ValueError(
                f"The endpoint '{call_endpoint}' "
                "is neither an attribute of the reloaded SavedModel, "
                "nor an entry in the `signatures` field of "
                "the reloaded SavedModel. Select another endpoint via "
                "the `call_endpoint` argument. Available endpoints for "
                "this SavedModel: "
                f"{list(self._reloaded_obj.signatures.keys())}"
            )

        # Resolving the training function.
        if call_training_endpoint:
            if hasattr(self._reloaded_obj, call_training_endpoint):
                self.call_training_endpoint_fn = getattr(
                    self._reloaded_obj, call_training_endpoint
                )
            elif call_training_endpoint in self._reloaded_obj.signatures:
                self.call_training_endpoint_fn = self._reloaded_obj.signatures[
                    call_training_endpoint
                ]
            else:
                raise ValueError(
                    f"The endpoint '{call_training_endpoint}' "
                    "is neither an attribute of the reloaded SavedModel, "
                    "nor an entry in the `signatures` field of "
                    "the reloaded SavedModel. Available endpoints for "
                    "this SavedModel: "
                    f"{list(self._reloaded_obj.signatures.keys())}"
                )

        # Add trainable and non-trainable weights from the call_endpoint_fn.
        all_fns = [self.call_endpoint_fn]
        if call_training_endpoint:
            all_fns.append(self.call_training_endpoint_fn)
        tvs, ntvs = _list_variables_used_by_fns(all_fns)
        for v in tvs:
            self._add_existing_weight(v)
        for v in ntvs:
            self._add_existing_weight(v)

        self._build_at_init()