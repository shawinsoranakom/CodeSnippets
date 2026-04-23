def get_content_text(self) -> Message:
        try:
            from jigsawstack import JigsawStack, JigsawStackError
        except ImportError:
            return Message(text="Error: JigsawStack package not found.")

        try:
            # Initialize JigsawStack client
            client = JigsawStack(api_key=self.api_key)
            search_params = {}
            if self.query:
                search_params["query"] = self.query
            if self.ai_overview is not None:
                search_params["ai_overview"] = self.ai_overview
            if self.safe_search:
                search_params["safe_search"] = self.safe_search
            if self.spell_check is not None:
                search_params["spell_check"] = self.spell_check

            # Call web scraping
            response = client.web.search(search_params)

            request_failed_msg = "Request Failed"
            if not response.get("success", False):
                raise JigsawStackError(request_failed_msg)

            # Return the content as text
            content = response.get("ai_overview", "")
            return Message(text=content)

        except JigsawStackError as e:
            return Message(text=f"Error while using AI Search: {e!s}")