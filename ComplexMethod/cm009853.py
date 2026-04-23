def test_load_llmchain_env() -> None:
    import os

    from langchain_openai import OpenAI

    has_env = "OPENAI_API_KEY" in os.environ
    if not has_env:
        os.environ["OPENAI_API_KEY"] = "env_variable"

    llm = CommunityOpenAI(model="davinci", temperature=0.5)
    prompt = PromptTemplate.from_template("hello {name}!")
    chain = LLMChain(llm=llm, prompt=prompt)
    chain_obj = dumpd(chain)
    chain2 = load(chain_obj)

    assert chain2 == chain
    assert dumpd(chain2) == chain_obj
    assert isinstance(chain2, LLMChain)
    assert isinstance(chain2.llm, OpenAI)
    assert isinstance(chain2.prompt, PromptTemplate)

    if not has_env:
        del os.environ["OPENAI_API_KEY"]