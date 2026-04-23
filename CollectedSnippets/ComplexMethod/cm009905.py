def create_qa_with_structure_chain(
    llm: BaseLanguageModel,
    schema: dict | type[BaseModel],
    output_parser: str = "base",
    prompt: PromptTemplate | ChatPromptTemplate | None = None,
    verbose: bool = False,  # noqa: FBT001,FBT002
) -> LLMChain:
    """Create a question answering chain with structure.

    Create a question answering chain that returns an answer with sources
    based on schema.

    Args:
        llm: Language model to use for the chain.
        schema: Pydantic schema to use for the output.
        output_parser: Output parser to use. Should be one of `'pydantic'` or `'base'`.
        prompt: Optional prompt to use for the chain.
        verbose: Whether to run the chain in verbose mode.

    Returns:
        The question answering chain.

    """
    if output_parser == "pydantic":
        if not (isinstance(schema, type) and is_basemodel_subclass(schema)):
            msg = (
                "Must provide a pydantic class for schema when output_parser is "
                "'pydantic'."
            )
            raise ValueError(msg)
        _output_parser: BaseLLMOutputParser = PydanticOutputFunctionsParser(
            pydantic_schema=schema,
        )
    elif output_parser == "base":
        _output_parser = OutputFunctionsParser()
    else:
        msg = (
            f"Got unexpected output_parser: {output_parser}. "
            f"Should be one of `pydantic` or `base`."
        )
        raise ValueError(msg)
    if isinstance(schema, type) and is_basemodel_subclass(schema):
        schema_dict = cast("dict", schema.model_json_schema())
    else:
        schema_dict = cast("dict", schema)
    function = {
        "name": schema_dict["title"],
        "description": schema_dict["description"],
        "parameters": schema_dict,
    }
    llm_kwargs = get_llm_kwargs(function)
    messages = [
        SystemMessage(
            content=(
                "You are a world class algorithm to answer "
                "questions in a specific format."
            ),
        ),
        HumanMessage(content="Answer question using the following context"),
        HumanMessagePromptTemplate.from_template("{context}"),
        HumanMessagePromptTemplate.from_template("Question: {question}"),
        HumanMessage(content="Tips: Make sure to answer in the correct format"),
    ]
    prompt = prompt or ChatPromptTemplate(messages=messages)  # type: ignore[arg-type]

    return LLMChain(
        llm=llm,
        prompt=prompt,
        llm_kwargs=llm_kwargs,
        output_parser=_output_parser,
        verbose=verbose,
    )