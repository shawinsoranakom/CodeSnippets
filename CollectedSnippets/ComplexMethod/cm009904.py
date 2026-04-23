def get_openapi_chain(
    spec: OpenAPISpec | str,
    llm: BaseLanguageModel | None = None,
    prompt: BasePromptTemplate | None = None,
    request_chain: Chain | None = None,
    llm_chain_kwargs: dict | None = None,
    verbose: bool = False,  # noqa: FBT001,FBT002
    headers: dict | None = None,
    params: dict | None = None,
    **kwargs: Any,
) -> SequentialChain:
    r"""Create a chain for querying an API from a OpenAPI spec.

    !!! warning "Deprecated"
        This function and all related utilities in this module are deprecated.
        Use LLM tool calling features directly with an HTTP client instead.

    Args:
        spec: OpenAPISpec or url/file/text string corresponding to one.
        llm: language model, should be an OpenAI function-calling model, e.g.
            `ChatOpenAI(model="gpt-3.5-turbo-0613")`.
        prompt: Main prompt template to use.
        request_chain: Chain for taking the functions output and executing the request.
        params: Request parameters.
        headers: Request headers.
        verbose: Whether to run the chain in verbose mode.
        llm_chain_kwargs: LLM chain additional keyword arguments.
        **kwargs: Additional keyword arguments to pass to the chain.

    """
    try:
        from langchain_community.utilities.openapi import OpenAPISpec
    except ImportError as e:
        msg = (
            "Could not import langchain_community.utilities.openapi. "
            "Please install it with `pip install langchain-community`."
        )
        raise ImportError(msg) from e
    if isinstance(spec, str):
        for conversion in (
            OpenAPISpec.from_url,
            OpenAPISpec.from_file,
            OpenAPISpec.from_text,
        ):
            try:
                spec = conversion(spec)
                break
            except ImportError:
                raise
            except Exception:  # noqa: BLE001
                _logger.debug(
                    "Parse spec failed for OpenAPISpec.%s",
                    conversion.__name__,
                    exc_info=True,
                )
        if isinstance(spec, str):
            msg = f"Unable to parse spec from source {spec}"
            raise ValueError(msg)  # noqa: TRY004
    openai_fns, call_api_fn = openapi_spec_to_openai_fn(spec)
    if not llm:
        msg = (
            "Must provide an LLM for this chain.For example,\n"
            "from langchain_openai import ChatOpenAI\n"
            "model = ChatOpenAI()\n"
        )
        raise ValueError(msg)
    prompt = prompt or ChatPromptTemplate.from_template(
        "Use the provided API's to respond to this user query:\n\n{query}",
    )
    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        llm_kwargs={"functions": openai_fns},
        output_parser=JsonOutputFunctionsParser(args_only=False),
        output_key="function",
        verbose=verbose,
        **(llm_chain_kwargs or {}),
    )
    request_chain = request_chain or SimpleRequestChain(
        request_method=lambda name, args: call_api_fn(
            name,
            args,
            headers=headers,
            params=params,
        ),
        verbose=verbose,
    )
    return SequentialChain(
        chains=[llm_chain, request_chain],
        input_variables=llm_chain.input_keys,
        output_variables=["response"],
        verbose=verbose,
        **kwargs,
    )