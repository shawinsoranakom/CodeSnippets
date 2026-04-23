def test_loads_llmchain_env() -> None:
    import os

    from langchain_openai import OpenAI

    has_env = "OPENAI_API_KEY" in os.environ
    if not has_env:
        os.environ["OPENAI_API_KEY"] = "env_variable"

    llm = OpenAI(model="davinci", temperature=0.5, top_p=0.8)
    prompt = PromptTemplate.from_template("hello {name}!")
    chain = LLMChain(llm=llm, prompt=prompt)
    chain_string = dumps(chain)
    chain2 = loads(chain_string)

    assert chain2 == chain
    assert dumps(chain2) == chain_string
    assert isinstance(chain2, LLMChain)
    assert isinstance(chain2.llm, OpenAI)
    assert isinstance(chain2.prompt, PromptTemplate)

    if not has_env:
        del os.environ["OPENAI_API_KEY"]