def compile_grammar(
        self, request_type: StructuredOutputOptions, grammar_spec: str
    ) -> StructuredOutputGrammar:
        character_level_parser: lmformatenforcer.CharacterLevelParser
        if request_type == StructuredOutputOptions.JSON:
            spec_dict = json.loads(grammar_spec)
            character_level_parser = lmformatenforcer.JsonSchemaParser(spec_dict)
        elif request_type == StructuredOutputOptions.JSON_OBJECT:
            character_level_parser = lmformatenforcer.JsonSchemaParser(None)
        elif request_type == StructuredOutputOptions.REGEX:
            character_level_parser = lmformatenforcer.RegexParser(grammar_spec)
        elif request_type == StructuredOutputOptions.CHOICE:
            choices = ast.literal_eval(grammar_spec)
            character_level_parser = lmformatenforcer.UnionParser(
                [lmformatenforcer.StringParser(choice) for choice in choices]
            )
        else:
            raise ValueError(
                f"Invalid request type for LM Format Enforcer backend({request_type!s})"
            )
        max_rollback_tokens = (
            self.vllm_config.speculative_config.num_speculative_tokens
            if self.vllm_config.speculative_config is not None
            else 0
        )

        if max_rollback_tokens > 0:
            raise ValueError(
                "LM Format Enforcer backend does not support speculative tokens"
            )

        token_enforcer = lmformatenforcer.TokenEnforcer(
            tokenizer_data=self.tokenizer_data,
            parser=character_level_parser,
        )
        return LMFormatEnforcerGrammar(token_enforcer)