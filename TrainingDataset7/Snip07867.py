def __init__(
        self,
        expression,
        query,
        *,
        config=None,
        start_sel=None,
        stop_sel=None,
        max_words=None,
        min_words=None,
        short_word=None,
        highlight_all=None,
        max_fragments=None,
        fragment_delimiter=None,
    ):
        if not hasattr(query, "resolve_expression"):
            query = SearchQuery(query)
        options = {
            "StartSel": start_sel,
            "StopSel": stop_sel,
            "MaxWords": max_words,
            "MinWords": min_words,
            "ShortWord": short_word,
            "HighlightAll": highlight_all,
            "MaxFragments": max_fragments,
            "FragmentDelimiter": fragment_delimiter,
        }
        self.options = {
            option: value for option, value in options.items() if value is not None
        }
        expressions = (expression, query)
        if config is not None:
            config = SearchConfig.from_parameter(config)
            expressions = (config, *expressions)
        super().__init__(*expressions)