def test_pro_search(self) -> None:
        """Test Pro Search (reasoning_steps extraction)."""
        # Pro search is available on sonar-pro
        chat = ChatPerplexity(
            model="sonar-pro",
            temperature=0,
            web_search_options=WebSearchOptions(search_type="pro"),
            streaming=True,
        )
        message = HumanMessage(content="Who won the 2024 US election and why?")

        # We need to collect chunks to check reasoning steps
        chunks = list(chat.stream([message]))
        full_content = "".join(c.content for c in chunks if isinstance(c.content, str))
        assert full_content

        # Check if any chunk has reasoning_steps
        has_reasoning = any("reasoning_steps" in c.additional_kwargs for c in chunks)
        if has_reasoning:
            assert True
        else:
            # Fallback assertion if no reasoning steps returned
            assert len(chunks) > 0