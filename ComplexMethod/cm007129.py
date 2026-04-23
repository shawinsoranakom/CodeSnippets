def search(self) -> Data:
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

            api_error_msg = "JigsawStack API returned unsuccessful response"
            if not response.get("success", False):
                raise ValueError(api_error_msg)

            # Create comprehensive data object
            result_data = {
                "query": self.query,
                "ai_overview": response.get("ai_overview", ""),
                "spell_fixed": response.get("spell_fixed", False),
                "is_safe": response.get("is_safe", True),
                "results": response.get("results", []),
                "success": True,
            }

            self.status = f"Search complete for: {response.get('query', '')}"

            return Data(data=result_data)

        except JigsawStackError as e:
            error_data = {"error": str(e), "success": False}
            self.status = f"Error: {e!s}"
            return Data(data=error_data)