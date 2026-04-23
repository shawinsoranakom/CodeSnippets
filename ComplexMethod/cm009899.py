def from_retrievers(
        cls,
        llm: BaseLanguageModel,
        retriever_infos: list[dict[str, Any]],
        default_retriever: BaseRetriever | None = None,
        default_prompt: PromptTemplate | None = None,
        default_chain: Chain | None = None,
        *,
        default_chain_llm: BaseLanguageModel | None = None,
        **kwargs: Any,
    ) -> MultiRetrievalQAChain:
        """Create a multi retrieval qa chain from an LLM and a default chain.

        Args:
            llm: The language model to use.
            retriever_infos: Dictionaries containing retriever information.
            default_retriever: Optional default retriever to use if no default chain
                is provided.
            default_prompt: Optional prompt template to use for the default retriever.
            default_chain: Optional default chain to use when router doesn't map input
                to one of the destinations.
            default_chain_llm: Optional language model to use if no default chain and
                no default retriever are provided.
            **kwargs: Additional keyword arguments to pass to the chain.

        Returns:
            An instance of the multi retrieval qa chain.
        """
        if default_prompt and not default_retriever:
            msg = (
                "`default_retriever` must be specified if `default_prompt` is "
                "provided. Received only `default_prompt`."
            )
            raise ValueError(msg)
        destinations = [f"{r['name']}: {r['description']}" for r in retriever_infos]
        destinations_str = "\n".join(destinations)
        router_template = MULTI_RETRIEVAL_ROUTER_TEMPLATE.format(
            destinations=destinations_str,
        )
        router_prompt = PromptTemplate(
            template=router_template,
            input_variables=["input"],
            output_parser=RouterOutputParser(next_inputs_inner_key="query"),
        )
        router_chain = LLMRouterChain.from_llm(llm, router_prompt)
        destination_chains = {}
        for r_info in retriever_infos:
            prompt = r_info.get("prompt")
            retriever = r_info["retriever"]
            chain = RetrievalQA.from_llm(llm, prompt=prompt, retriever=retriever)
            name = r_info["name"]
            destination_chains[name] = chain
        if default_chain:
            _default_chain = default_chain
        elif default_retriever:
            _default_chain = RetrievalQA.from_llm(
                llm,
                prompt=default_prompt,
                retriever=default_retriever,
            )
        else:
            prompt_template = DEFAULT_TEMPLATE.replace("input", "query")
            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["history", "query"],
            )
            if default_chain_llm is None:
                msg = (
                    "conversation_llm must be provided if default_chain is not "
                    "specified. This API has been changed to avoid instantiating "
                    "default LLMs on behalf of users."
                    "You can provide a conversation LLM like so:\n"
                    "from langchain_openai import ChatOpenAI\n"
                    "model = ChatOpenAI()"
                )
                raise NotImplementedError(msg)
            _default_chain = ConversationChain(
                llm=default_chain_llm,
                prompt=prompt,
                input_key="query",
                output_key="result",
            )
        return cls(
            router_chain=router_chain,
            destination_chains=destination_chains,
            default_chain=_default_chain,
            **kwargs,
        )