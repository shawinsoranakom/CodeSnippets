async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        logger.debug(f"Starting AIListGeneratorBlock.run with input data: {input_data}")

        # Create a proper expected format for the structured response generator
        expected_format = {
            "list": "A JSON array containing the generated string values"
        }
        if input_data.force_json_output:
            # Add reasoning field for better performance
            expected_format = {
                "reasoning": "... (optional)",
                **expected_format,
            }

        # Build the prompt
        if input_data.focus:
            prompt = f"Generate a list with the following focus:\n<focus>\n\n{input_data.focus}</focus>"
        else:
            # If there's source data
            if input_data.source_data:
                prompt = "Extract the main focus of the source data to a list.\ni.e if the source data is a news website, the focus would be the news stories rather than the social links in the footer."
            else:
                # No focus or source data provided, generate a random list
                prompt = "Generate a random list."

        # If the source data is provided, add it to the prompt
        if input_data.source_data:
            prompt += f"\n\nUse the following source data to generate the list from:\n\n<source_data>\n\n{input_data.source_data}</source_data>\n\nDo not invent fictional data that is not present in the source data."
        # Else, tell the LLM to synthesize the data
        else:
            prompt += "\n\nInvent the data to generate the list from."

        # Use the structured response generator to handle all the complexity
        response_obj = await self.llm_call(
            AIStructuredResponseGeneratorBlock.Input(
                sys_prompt=self.SYSTEM_PROMPT,
                prompt=prompt,
                credentials=input_data.credentials,
                model=input_data.model,
                expected_format=expected_format,
                force_json_output=input_data.force_json_output,
                retry=input_data.max_retries,
                max_tokens=input_data.max_tokens,
                ollama_host=input_data.ollama_host,
            ),
            credentials=credentials,
        )
        logger.debug(f"Response object: {response_obj}")

        # Extract the list from the response object
        if isinstance(response_obj, dict) and "list" in response_obj:
            parsed_list = response_obj["list"]
        else:
            # Fallback - treat the whole response as the list
            parsed_list = response_obj

        # Validate that we got a list
        if not isinstance(parsed_list, list):
            raise ValueError(
                f"Expected a list, but got {type(parsed_list).__name__}: {parsed_list}"
            )

        logger.debug(f"Parsed list: {parsed_list}")

        # Yield the results
        yield "generated_list", parsed_list
        yield "prompt", self.prompt

        # Yield each item in the list
        for item in parsed_list:
            yield "list_item", item