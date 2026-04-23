def default_response(self) -> Message:
        """Handle the else case when no conditions match."""
        enable_else = getattr(self, "enable_else_output", False)
        if not enable_else:
            self.status = "Else output is disabled"
            return Message(text="")

        categories = getattr(self, "routes", [])
        input_text = getattr(self, "input_text", "")

        # Get the cached categorization result (performs LLM call only if not already done)
        categorization = self._get_categorization()

        # Check if the categorization matches any category
        has_match = False
        for i, category in enumerate(categories):
            route_category = category.get("route_category", "")
            if categorization.lower() == route_category.lower():
                has_match = True
                self.status = f"Match found for '{categorization}' (Category {i + 1}), stopping default_response"
                break

        if has_match:
            # A case matches, stop this output
            self.stop("default_result")
            return Message(text="")

        # No case matches, check for override output first, then use input as default
        override_output = getattr(self, "message", None)
        if (
            override_output
            and hasattr(override_output, "text")
            and override_output.text
            and str(override_output.text).strip()
        ):
            self.status = "Routed to Else (no match) - using override output"
            return Message(text=str(override_output.text))
        if override_output and isinstance(override_output, str) and override_output.strip():
            self.status = "Routed to Else (no match) - using override output"
            return Message(text=str(override_output))

        self.status = "Routed to Else (no match) - using input as default"
        return Message(text=input_text)