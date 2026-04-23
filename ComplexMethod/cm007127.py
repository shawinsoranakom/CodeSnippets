def detect_objects(self) -> Data:
        try:
            from jigsawstack import JigsawStack, JigsawStackError
        except ImportError as e:
            jigsawstack_import_error = (
                "JigsawStack package not found. Please install it using: pip install jigsawstack>=0.2.7"
            )
            raise ImportError(jigsawstack_import_error) from e

        try:
            client = JigsawStack(api_key=self.api_key)

            # build request object
            params = {}
            if self.prompts:
                if isinstance(self.prompts, list):
                    params["prompt"] = self.prompts
                elif isinstance(self.prompts, str):
                    if "," in self.prompts:
                        # Split by comma and strip whitespace
                        params["prompt"] = [p.strip() for p in self.prompts.split(",")]
                    else:
                        params["prompt"] = [self.prompts.strip()]
                else:
                    invalid_prompt_error = "Prompt must be a list of strings or a single string"
                    raise ValueError(invalid_prompt_error)
            if self.url:
                params["url"] = self.url
            if self.file_store_key:
                params["file_store_key"] = self.file_store_key

            # if both url and file_store_key are not provided, raise an error
            if not self.url and not self.file_store_key:
                missing_url_error = "Either URL or File Store Key must be provided to perform object detection"
                raise ValueError(missing_url_error)

            params["annotated_image"] = self.annotated_image
            if self.features:
                params["features"] = self.features

            # Call web scraping
            response = client.vision.object_detection(params)

            if not response.get("success", False):
                failed_response_error = "JigsawStack API returned unsuccessful response"
                raise ValueError(failed_response_error)

            return Data(data=response)

        except JigsawStackError as e:
            error_data = {"error": str(e), "success": False}
            self.status = f"Error: {e!s}"
            return Data(data=error_data)