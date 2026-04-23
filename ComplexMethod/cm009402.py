def build_extra(cls, values: dict[str, Any]) -> Any:
        """Build extra kwargs from additional params that were passed in."""
        all_required_field_names = get_pydantic_field_names(cls)
        extra = values.get("model_kwargs", {})
        for field_name in list(values):
            if field_name in extra:
                msg = f"Found {field_name} supplied twice."
                raise ValueError(msg)
            if field_name not in all_required_field_names:
                logger.warning(
                    f"""WARNING! {field_name} is not default parameter.
                    {field_name} was transferred to model_kwargs.
                    Please make sure that {field_name} is what you intended."""
                )
                extra[field_name] = values.pop(field_name)

        invalid_model_kwargs = all_required_field_names.intersection(extra.keys())
        if invalid_model_kwargs:
            msg = (
                f"Parameters {invalid_model_kwargs} should be specified explicitly. "
                f"Instead they were passed in as part of `model_kwargs` parameter."
            )
            raise ValueError(msg)

        values["model_kwargs"] = extra

        # to correctly create the InferenceClient and AsyncInferenceClient
        # in validate_environment, we need to populate values["model"].
        # from InferenceClient docstring:
        # model (`str`, `optional`):
        #     The model to run inference with. Can be a model id hosted on the Hugging
        #       Face Hub, e.g. `bigcode/starcoder`
        #     or a URL to a deployed Inference Endpoint. Defaults to `None`, in which
        #       case a recommended model is
        #     automatically selected for the task.

        # this string could be in 3 places of descending priority:
        # 2. values["model"] or values["endpoint_url"] or values["repo_id"]
        #       (equal priority - don't allow both set)
        # 3. values["HF_INFERENCE_ENDPOINT"] (if none above set)

        model = values.get("model")
        endpoint_url = values.get("endpoint_url")
        repo_id = values.get("repo_id")

        if repo_id and repo_id.startswith(("http://", "https://")):
            msg = (
                "`repo_id` must be a HuggingFace repo ID, not a URL. "
                "Use `endpoint_url` for direct endpoints."
            )
            raise ValueError(msg)

        if sum([bool(model), bool(endpoint_url), bool(repo_id)]) > 1:
            msg = (
                "Please specify either a `model` OR an `endpoint_url` OR a `repo_id`,"
                "not more than one."
            )
            raise ValueError(msg)
        values["model"] = (
            model or endpoint_url or repo_id or os.environ.get("HF_INFERENCE_ENDPOINT")
        )
        if not values["model"]:
            msg = (
                "Please specify a `model` or an `endpoint_url` or a `repo_id` for the "
                "model."
            )
            raise ValueError(msg)
        return values