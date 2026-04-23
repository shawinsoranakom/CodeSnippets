def main(args: Namespace):
    # Run the selected reranker model
    model_request = model_example_map[args.model_name]()
    engine_args = model_request.engine_args

    llm = LLM.from_engine_args(engine_args)

    print("Query: string & Document: string")
    outputs = llm.score(query, document)
    print("Relevance scores:", [output.outputs.score for output in outputs])

    print("Query: string & Document: text")
    outputs = llm.score(
        query, {"content": [documents[0]]}, chat_template=model_request.chat_template
    )
    print("Relevance scores:", [output.outputs.score for output in outputs])

    print("Query: string & Document: image url")
    outputs = llm.score(
        query, {"content": [documents[1]]}, chat_template=model_request.chat_template
    )
    print("Relevance scores:", [output.outputs.score for output in outputs])

    print("Query: string & Document: image base64")
    outputs = llm.score(
        query, {"content": [documents[2]]}, chat_template=model_request.chat_template
    )
    print("Relevance scores:", [output.outputs.score for output in outputs])

    if "video" in model_request.modality:
        print("Query: string & Document: video url")
        outputs = llm.score(
            query,
            {"content": [documents[3]]},
            chat_template=model_request.chat_template,
        )
        print("Relevance scores:", [output.outputs.score for output in outputs])

    print("Query: string & Document: text + image url")
    outputs = llm.score(
        query,
        {"content": [documents[0], documents[1]]},
        chat_template=model_request.chat_template,
    )
    print("Relevance scores:", [output.outputs.score for output in outputs])

    print("Query: string & Document: list")
    outputs = llm.score(
        query,
        [
            document,
            {"content": [documents[0]]},
            {"content": [documents[1]]},
            {"content": [documents[0], documents[1]]},
        ],
        chat_template=model_request.chat_template,
    )
    print("Relevance scores:", [output.outputs.score for output in outputs])