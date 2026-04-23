def compile_grammar(
        self, request_type: StructuredOutputOptions, grammar_spec: str
    ) -> StructuredOutputGrammar:
        if request_type == StructuredOutputOptions.JSON:
            ctx = self.compiler.compile_json_schema(
                grammar_spec, any_whitespace=not self.disable_any_whitespace
            )
        elif request_type == StructuredOutputOptions.JSON_OBJECT:
            ctx = self.compiler.compile_json_schema(
                '{"type": "object"}', any_whitespace=not self.disable_any_whitespace
            )
        elif request_type == StructuredOutputOptions.GRAMMAR:
            ctx = self.compiler.compile_grammar(grammar_spec)
        elif request_type == StructuredOutputOptions.REGEX:
            ctx = self.compiler.compile_regex(grammar_spec)
        elif request_type == StructuredOutputOptions.STRUCTURAL_TAG:
            s_tag = json.loads(grammar_spec)
            if "structures" in s_tag:
                # Falling back to deprecated method of compiling structural tag
                tags = [
                    xgr.StructuralTagItem(
                        begin=s["begin"],
                        schema=json.dumps(s["schema"]),
                        end=s["end"],
                    )
                    for s in s_tag["structures"]
                ]
                ctx = self.compiler.compile_structural_tag(tags, s_tag["triggers"])
            else:
                ctx = self.compiler.compile_structural_tag(grammar_spec)
        else:
            logger.error(
                "Validation should have already occurred. Please file an issue."
            )
            raise ValueError(
                f"grammar is not of valid supported types. ({request_type!s})"
            )

        return XgrammarGrammar(
            matcher=xgr.GrammarMatcher(
                ctx,
                max_rollback_tokens=self.num_speculative_tokens,
            ),
            vocab_size=self.vocab_size,
            ctx=ctx,
        )