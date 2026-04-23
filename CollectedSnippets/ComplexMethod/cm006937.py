def _build_search_args(self):
        args = {
            "k": self.number_of_results,
            "score_threshold": self.search_score_threshold,
        }

        if self.search_filter:
            clean_filter = {k: v for k, v in self.search_filter.items() if k and v}
            if len(clean_filter) > 0:
                args["filter"] = clean_filter
        if self.body_search:
            if not self.enable_body_search:
                msg = "You should enable body search when creating the table to search the body field."
                raise ValueError(msg)
            args["body_search"] = self.body_search
        return args