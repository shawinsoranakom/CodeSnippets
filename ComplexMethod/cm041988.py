def retrieve(self, context: str, exp_type: Literal["plan", "task"] = "plan") -> str:
        if exp_type == "plan":
            if "deploy" in context.lower():
                return DEPLOY_EXAMPLE
            elif "issue" in context.lower():
                return FIX_ISSUE_EXAMPLE
            elif "https:" in context.lower() or "http:" in context.lower() or "search" in context.lower():
                if "search" in context.lower() or "click" in context.lower():
                    return WEB_SCRAPING_EXAMPLE
                return WEB_SCRAPING_EXAMPLE_SIMPLE
        # elif exp_type == "task":
        #     if "diagnose" in context.lower():
        #         return SEARCH_SYMBOL_EXAMPLE
        return ""