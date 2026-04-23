def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        try:
            from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse
        except ImportError as e:
            msg = "langchain_aws is not installed. Please install it with `pip install langchain_aws`."
            raise ImportError(msg) from e

        # Prepare initialization parameters
        init_params = {
            "model": self.model_id,
            "region_name": self.region_name,
        }

        # Add AWS credentials if provided
        if self.aws_access_key_id:
            init_params["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            init_params["aws_secret_access_key"] = self.aws_secret_access_key
        if self.aws_session_token:
            init_params["aws_session_token"] = self.aws_session_token
        if self.credentials_profile_name:
            init_params["credentials_profile_name"] = self.credentials_profile_name
        if self.endpoint_url:
            init_params["endpoint_url"] = self.endpoint_url

        # Add model parameters directly as supported by ChatBedrockConverse
        if hasattr(self, "temperature") and self.temperature is not None:
            init_params["temperature"] = self.temperature
        if hasattr(self, "max_tokens") and self.max_tokens is not None:
            init_params["max_tokens"] = self.max_tokens
        if hasattr(self, "top_p") and self.top_p is not None:
            init_params["top_p"] = self.top_p

        # Handle streaming - only disable if explicitly requested
        if hasattr(self, "disable_streaming") and self.disable_streaming:
            init_params["disable_streaming"] = True

        # Handle additional model request fields carefully
        # Based on the error, inferenceConfig should not be passed as additional fields for some models
        additional_model_request_fields = {}

        # Only add top_k if user explicitly provided additional fields or if needed for specific models
        if hasattr(self, "additional_model_fields") and self.additional_model_fields:
            for field in self.additional_model_fields:
                if isinstance(field, dict):
                    additional_model_request_fields.update(field)

        # For now, don't automatically add inferenceConfig for top_k to avoid validation errors
        # Users can manually add it via additional_model_fields if their model supports it

        # Only add if we have actual additional fields
        if additional_model_request_fields:
            init_params["additional_model_request_fields"] = additional_model_request_fields

        try:
            output = ChatBedrockConverse(**init_params)
        except Exception as e:
            # Provide helpful error message with fallback suggestions
            error_details = str(e)
            if "validation error" in error_details.lower():
                msg = (
                    f"ChatBedrockConverse validation error: {error_details}. "
                    f"This may be due to incompatible parameters for model '{self.model_id}'. "
                    f"Consider adjusting the model parameters or trying the legacy Amazon Bedrock component."
                )
            elif "converse api" in error_details.lower():
                msg = (
                    f"Converse API error: {error_details}. "
                    f"The model '{self.model_id}' may not support the Converse API. "
                    f"Try using the legacy Amazon Bedrock component instead."
                )
            else:
                msg = f"Could not initialize ChatBedrockConverse: {error_details}"
            raise ValueError(msg) from e

        return output