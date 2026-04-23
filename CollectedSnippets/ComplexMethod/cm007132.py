def vocr(self) -> Data:
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

            if self.page_range_start and self.page_range_end:
                params["page_range"] = [self.page_range_start, self.page_range_end]

            # Call VOCR
            response = client.vision.vocr(params)

            if not response.get("success", False):
                failed_response_error = "JigsawStack API returned unsuccessful response"
                raise ValueError(failed_response_error)

            return Data(data=response)

        except JigsawStackError as e:
            error_data = {"error": str(e), "success": False}
            self.status = f"Error: {e!s}"
            return Data(data=error_data)