def generate_pattern(
        label: str,
        html: str,
        *,
        query: Optional[str] = None,
        examples: Optional[List[str]] = None,
        llm_config: Optional[LLMConfig] = None,
        **kwargs,
    ) -> Dict[str, str]:
        """
        Ask an LLM for a single page-specific regex and return
            {label: pattern}   ── ready for RegexExtractionStrategy(custom=…)
        """

        # ── guard deprecated kwargs
        for k in RegexExtractionStrategy._UNWANTED_PROPS:
            if k in kwargs:
                raise AttributeError(
                    f"{k} is deprecated, {RegexExtractionStrategy._UNWANTED_PROPS[k]}"
                )

        # ── default LLM config
        if llm_config is None:
            llm_config = create_llm_config()

        # ── system prompt – hardened
        system_msg = (
            "You are an expert Python-regex engineer.\n"
            f"Return **one** JSON object whose single key is exactly \"{label}\", "
            "and whose value is a raw-string regex pattern that works with "
            "the standard `re` module in Python.\n\n"
            "Strict rules (obey every bullet):\n"
            "• If a *user query* is supplied, treat it as the precise semantic target and optimise the "
            "  pattern to capture ONLY text that answers that query. If the query conflicts with the "
            "  sample HTML, the HTML wins.\n"
            "• Tailor the pattern to the *sample HTML* – reproduce its exact punctuation, spacing, "
            "  symbols, capitalisation, etc. Do **NOT** invent a generic form.\n"
            "• Keep it minimal and fast: avoid unnecessary capturing, prefer non-capturing `(?: … )`, "
            "  and guard against catastrophic backtracking.\n"
            "• Anchor with `^`, `$`, or `\\b` only when it genuinely improves precision.\n"
            "• Use inline flags like `(?i)` when needed; no verbose flag comments.\n"
            "• Output must be valid JSON – no markdown, code fences, comments, or extra keys.\n"
            "• The regex value must be a Python string literal: **double every backslash** "
            "(e.g. `\\\\b`, `\\\\d`, `\\\\\\\\`).\n\n"
            "Example valid output:\n"
            f"{{\"{label}\": \"(?:RM|rm)\\\\s?\\\\d{{1,3}}(?:,\\\\d{{3}})*(?:\\\\.\\\\d{{2}})?\"}}"
        )

        # ── user message: cropped HTML + optional hints
        user_parts = ["```html", html[:5000], "```"]  # protect token budget
        if query:
            user_parts.append(f"\n\n## Query\n{query.strip()}")
        if examples:
            user_parts.append("## Examples\n" + "\n".join(examples[:20]))
        user_msg = "\n\n".join(user_parts)

        # ── LLM call (with retry/backoff)
        resp = perform_completion_with_backoff(
            provider=llm_config.provider,
            prompt_with_variables="\n\n".join([system_msg, user_msg]),
            json_response=True,
            api_token=llm_config.api_token,
            base_url=llm_config.base_url,
            extra_args=kwargs,
        )

        # ── clean & load JSON (fix common escape mistakes *before* json.loads)
        raw = resp.choices[0].message.content
        raw = raw.replace("\x08", "\\b")                     # stray back-space → \b
        raw = re.sub(r'(?<!\\)\\(?![\\u"])', r"\\\\", raw)   # lone \ → \\

        try:
            pattern_dict = json.loads(raw)
        except Exception as exc:
            raise ValueError(f"LLM did not return valid JSON: {raw}") from exc

        # quick sanity-compile
        for lbl, pat in pattern_dict.items():
            try:
                re.compile(pat)
            except re.error as e:
                raise ValueError(f"Invalid regex for '{lbl}': {e}") from None

        return pattern_dict