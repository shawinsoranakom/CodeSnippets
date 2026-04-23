def process_case(self) -> Message:
        """Process all categories using LLM categorization and return message for matching category."""
        # Clear any previous match state (only on first call)
        if self._categorization_result is None:
            self._matched_category = None

        # Get categories and input text
        categories = getattr(self, "routes", [])
        input_text = getattr(self, "input_text", "")

        # Get the cached categorization result (performs LLM call only once)
        categorization = self._get_categorization()

        # Find matching category based on LLM response
        matched_category = None
        for i, category in enumerate(categories):
            route_category = category.get("route_category", "")
            if categorization.lower() == route_category.lower():
                matched_category = i
                self.status = f"MATCH FOUND! Category {i + 1} matched with '{categorization}'"
                break

        if matched_category is not None:
            # Store the matched category for other outputs to check
            self._matched_category = matched_category

            # Stop all category outputs except the matched one
            for i in range(len(categories)):
                if i != matched_category:
                    self.stop(f"category_{i + 1}_result")

            # Also stop the default output (if it exists)
            enable_else = getattr(self, "enable_else_output", False)
            if enable_else:
                self.stop("default_result")

            route_category = categories[matched_category].get("route_category", f"Category {matched_category + 1}")
            self.status = f"Categorized as {route_category}"

            # Check if there's an override output (takes precedence over everything)
            override_output = getattr(self, "message", None)
            if (
                override_output
                and hasattr(override_output, "text")
                and override_output.text
                and str(override_output.text).strip()
            ):
                return Message(text=str(override_output.text))
            if override_output and isinstance(override_output, str) and override_output.strip():
                return Message(text=str(override_output))

            # Check if there's a custom output value for this category
            custom_output = categories[matched_category].get("output_value", "")
            # Treat None, empty string, or whitespace as blank
            if custom_output and str(custom_output).strip() and str(custom_output).strip().lower() != "none":
                # Use custom output value
                return Message(text=str(custom_output))
            # Use input as default output
            return Message(text=input_text)
        # No match found, stop all category outputs
        for i in range(len(categories)):
            self.stop(f"category_{i + 1}_result")

        # Check if else output is enabled
        enable_else = getattr(self, "enable_else_output", False)
        if enable_else:
            # The default_response will handle the else case
            self.stop("process_case")
            return Message(text="")
        # No else output, so no output at all
        self.status = "No match found and Else output is disabled"
        return Message(text="")