def from_model_id(
        cls,
        model_id: str,
        task: str | None = None,
        backend: Literal["pipeline", "endpoint", "text-gen"] = "pipeline",
        **kwargs: Any,
    ) -> ChatHuggingFace:
        """Construct a ChatHuggingFace model from a model_id.

        Args:
            model_id: The model ID of the Hugging Face model.
            task: The task to perform (e.g., "text-generation").
            backend: The backend to use. One of "pipeline", "endpoint", "text-gen".
            **kwargs: Additional arguments to pass to the backend or ChatHuggingFace.
        """
        llm: (
            Any  # HuggingFacePipeline, HuggingFaceEndpoint, HuggingFaceTextGenInference
        )
        if backend == "pipeline":
            from langchain_huggingface.llms.huggingface_pipeline import (
                HuggingFacePipeline,
            )

            task = task if task is not None else "text-generation"

            # Separate pipeline-specific kwargs from ChatHuggingFace kwargs
            # Parameters that should go to HuggingFacePipeline.from_model_id
            pipeline_specific_kwargs = {}

            # Extract pipeline-specific parameters
            pipeline_keys = [
                "backend",
                "device",
                "device_map",
                "model_kwargs",
                "pipeline_kwargs",
                "batch_size",
            ]
            for key in pipeline_keys:
                if key in kwargs:
                    pipeline_specific_kwargs[key] = kwargs.pop(key)

            # Remaining kwargs (temperature, max_tokens, etc.) should go to
            # pipeline_kwargs for generation parameters, which ChatHuggingFace
            # will inherit from the LLM
            if "pipeline_kwargs" not in pipeline_specific_kwargs:
                pipeline_specific_kwargs["pipeline_kwargs"] = {}

            # Add generation parameters to pipeline_kwargs
            # Map max_tokens to max_new_tokens for HuggingFace pipeline
            generation_params = {}
            for k, v in list(kwargs.items()):
                if k == "max_tokens":
                    generation_params["max_new_tokens"] = v
                    kwargs.pop(k)
                elif k in (
                    "temperature",
                    "max_new_tokens",
                    "top_p",
                    "top_k",
                    "repetition_penalty",
                    "do_sample",
                ):
                    generation_params[k] = v
                    kwargs.pop(k)

            pipeline_specific_kwargs["pipeline_kwargs"].update(generation_params)

            # Create the HuggingFacePipeline
            llm = HuggingFacePipeline.from_model_id(
                model_id=model_id, task=task, **pipeline_specific_kwargs
            )
        elif backend == "endpoint":
            from langchain_huggingface.llms.huggingface_endpoint import (
                HuggingFaceEndpoint,
            )

            llm = HuggingFaceEndpoint(repo_id=model_id, task=task, **kwargs)
        elif backend == "text-gen":
            from langchain_community.llms.huggingface_text_gen_inference import (  # type: ignore[import-not-found]
                HuggingFaceTextGenInference,
            )

            llm = HuggingFaceTextGenInference(inference_server_url=model_id, **kwargs)
        else:
            msg = f"Unknown backend: {backend}"
            raise ValueError(msg)

        return cls(llm=llm, **kwargs)