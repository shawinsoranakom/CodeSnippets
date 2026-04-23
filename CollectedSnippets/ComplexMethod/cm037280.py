def validate_xgrammar_grammar(sampling_params: SamplingParams) -> None:
    """Validate that the request is supported by structured output.

    Raises ValueError if the request is not supported.
    """
    if sampling_params.structured_outputs is None:
        return

    so_params = sampling_params.structured_outputs

    if so_params.regex:
        try:
            xgr.Grammar.from_regex(so_params.regex)
        except Exception as err:
            raise ValueError(
                f"Failed to transform regex into a grammar: {err}"
            ) from err

    if so_params.choice:
        choice_grammar = choice_as_grammar(so_params.choice)
        try:
            xgr.Grammar.from_ebnf(choice_grammar)
        except Exception as err:
            raise ValueError(
                f"Failed to transform choices into a grammar: {err}"
            ) from err
        so_params.choice = None
        so_params.grammar = choice_grammar
        return

    if so_params.json:
        if isinstance(so_params.json, str):
            try:
                schema = json.loads(so_params.json)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON grammar specification.") from e
        else:
            schema = so_params.json

        if has_xgrammar_unsupported_json_features(schema):
            raise ValueError(
                "The provided JSON schema contains features not supported by xgrammar."
            )

        try:
            xgr.Grammar.from_json_schema(schema)
        except Exception as err:
            raise ValueError(
                f"Failed to transform json schema into a grammar: {err}"
            ) from err
        return

    if so_params.grammar:
        if grammar_is_likely_lark(so_params.grammar):
            # xgrammar supports EBNF grammars only
            try:
                so_params.grammar = convert_lark_to_ebnf(so_params.grammar)
            except ValueError as e:
                raise ValueError(
                    "Failed to convert the grammar from Lark to EBNF. "
                ) from e

        # Test parsing EBNF grammar, possibly already converted from Lark
        try:
            # parse the grammar, but we aren't compiling it.
            xgr.Grammar.from_ebnf(so_params.grammar)
        except Exception as e:
            raise ValueError("Invalid grammar specification.") from e
        return

    if so_params.structural_tag:
        try:
            s_tag = json.loads(so_params.structural_tag)

            # Using the deprecated method of compiling structural tag
            if "structures" in s_tag:
                tags = [
                    xgr.StructuralTagItem(
                        begin=s["begin"],
                        schema=json.dumps(s["schema"]),
                        end=s["end"],
                    )
                    for s in s_tag["structures"]
                ]
                xgr.Grammar.from_structural_tag(tags, s_tag["triggers"])
            else:
                xgr.Grammar.from_structural_tag(so_params.structural_tag)
        except Exception as e:
            raise ValueError("Invalid structural tag specification.") from e