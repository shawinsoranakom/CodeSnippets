def _default_params(self) -> dict[str, Any]:
        """Get the default parameters for calling PerplexityChat API."""
        params: dict[str, Any] = {
            "max_tokens": self.max_tokens,
            "stream": self.streaming,
            "temperature": self.temperature,
        }
        if self.search_mode:
            params["search_mode"] = self.search_mode
        if self.reasoning_effort:
            params["reasoning_effort"] = self.reasoning_effort
        if self.language_preference:
            params["language_preference"] = self.language_preference
        if self.search_domain_filter:
            params["search_domain_filter"] = self.search_domain_filter
        if self.return_images:
            params["return_images"] = self.return_images
        if self.return_related_questions:
            params["return_related_questions"] = self.return_related_questions
        if self.search_recency_filter:
            params["search_recency_filter"] = self.search_recency_filter
        if self.search_after_date_filter:
            params["search_after_date_filter"] = self.search_after_date_filter
        if self.search_before_date_filter:
            params["search_before_date_filter"] = self.search_before_date_filter
        if self.last_updated_after_filter:
            params["last_updated_after_filter"] = self.last_updated_after_filter
        if self.last_updated_before_filter:
            params["last_updated_before_filter"] = self.last_updated_before_filter
        if self.disable_search:
            params["disable_search"] = self.disable_search
        if self.enable_search_classifier:
            params["enable_search_classifier"] = self.enable_search_classifier
        if self.web_search_options:
            params["web_search_options"] = self.web_search_options.model_dump(
                exclude_none=True
            )
        if self.media_response:
            if "extra_body" not in params:
                params["extra_body"] = {}
            params["extra_body"]["media_response"] = self.media_response.model_dump(
                exclude_none=True
            )

        return {**params, **self.model_kwargs}