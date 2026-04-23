def _get_categorization(self) -> str:
        """Perform LLM categorization and cache the result.

        This ensures the LLM is called only once per component execution,
        regardless of how many outputs are connected.
        """
        # Return cached result if available
        if self._categorization_result is not None:
            return self._categorization_result

        categories = getattr(self, "routes", [])
        input_text = getattr(self, "input_text", "")
        llm = get_llm(model=self.model, user_id=self.user_id, api_key=self.api_key)

        if not llm or not categories:
            self.status = "No LLM provided for categorization"
            self._categorization_result = "NONE"
            return self._categorization_result

        # Create prompt for categorization
        category_info = []
        for i, category in enumerate(categories):
            cat_name = category.get("route_category", f"Category {i + 1}")
            cat_desc = category.get("route_description", "")
            if cat_desc and cat_desc.strip():
                category_info.append(f'"{cat_name}": {cat_desc}')
            else:
                category_info.append(f'"{cat_name}"')

        categories_text = "\n".join([f"- {info}" for info in category_info if info])

        # Create base prompt
        base_prompt = (
            f"You are a text classifier. Given the following text and categories, "
            f"determine which category best matches the text.\n\n"
            f'Text to classify: "{input_text}"\n\n'
            f"Available categories:\n{categories_text}\n\n"
            f"Respond with ONLY the exact category name that best matches the text. "
            f'If none match well, respond with "NONE".\n\n'
            f"Category:"
        )

        # Use custom prompt as additional instructions if provided
        custom_prompt = getattr(self, "custom_prompt", "")
        if custom_prompt and custom_prompt.strip():
            self.status = "Using custom prompt as additional instructions"
            simple_routes = ", ".join(
                [f'"{cat.get("route_category", f"Category {i + 1}")}"' for i, cat in enumerate(categories)]
            )
            formatted_custom = custom_prompt.format(input_text=input_text, routes=simple_routes)
            prompt = f"{base_prompt}\n\nAdditional Instructions:\n{formatted_custom}"
        else:
            self.status = "Using default prompt for LLM categorization"
            prompt = base_prompt

        self.status = f"Prompt sent to LLM:\n{prompt}"

        try:
            if hasattr(llm, "invoke"):
                response = llm.invoke(prompt)
                self._token_usage = extract_usage_from_message(response)
                if hasattr(response, "content"):
                    categorization = response.content.strip().strip('"')
                else:
                    categorization = str(response).strip().strip('"')
            else:
                categorization = str(llm(prompt)).strip().strip('"')

            self.status = f"LLM response: '{categorization}'"
            self._categorization_result = categorization
        except RuntimeError as e:
            self.status = f"Error in LLM categorization: {e!s}"
            self._categorization_result = "NONE"

        return self._categorization_result