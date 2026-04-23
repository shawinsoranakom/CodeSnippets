async def _run_client(
        self, credentials: APIKeyCredentials, model_name: str, input_params: dict
    ):
        try:
            # Initialize Replicate client
            client = ReplicateClient(api_token=credentials.api_key.get_secret_value())

            # Run the model with input parameters
            output = await client.async_run(model_name, input=input_params, wait=False)

            # Process output
            if isinstance(output, list) and len(output) > 0:
                if isinstance(output[0], FileOutput):
                    result_url = output[0].url
                else:
                    result_url = output[0]
            elif isinstance(output, FileOutput):
                result_url = output.url
            elif isinstance(output, str):
                result_url = output
            else:
                result_url = None

            return result_url

        except TypeError as e:
            raise TypeError(f"Error during model execution: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during model execution: {e}")