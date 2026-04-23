def _run_vllm_reranker(
    vllm_runner: type[VllmRunner],
    model: str,
    dtype: str,
    query: str,
    docs: list,
) -> list[float]:
    """Run vLLM reranker inference; docs is a list of (doc_text, doc_image|None)."""
    with vllm_runner(
        model,
        runner="pooling",
        dtype=dtype,
        max_model_len=2048,
        enforce_eager=True,
        trust_remote_code=True,
        **ROCM_ENGINE_KWARGS,
    ) as vllm_model:
        has_images = any(img is not None for _, img in docs)

        if not has_images:
            # Text-only path: use the simple string score API.
            queries = [query] * len(docs)
            doc_texts = [doc_text for doc_text, _ in docs]
            outputs = vllm_model.score(
                queries,
                doc_texts,
                chat_template=_RERANKER_SCORE_TEMPLATE,
            )
        else:
            # Multimodal path: build ScoreMultiModalParam for each pair.
            query_params = [
                ScoreMultiModalParam(
                    content=[
                        ChatCompletionContentPartTextParam(
                            type="text",
                            text=query,
                        )
                    ]
                )
            ] * len(docs)

            doc_params = []
            for doc_text, doc_image in docs:
                content: list = []
                if doc_image is not None:
                    content.append(
                        ChatCompletionContentPartImageParam(
                            type="image_url",
                            image_url={"url": _pil_to_data_uri(doc_image)},
                        )
                    )
                if doc_text:
                    content.append(
                        ChatCompletionContentPartTextParam(
                            type="text",
                            text=doc_text,
                        )
                    )
                doc_params.append(ScoreMultiModalParam(content=content))

            raw_outputs = vllm_model.llm.score(
                query_params,
                doc_params,
                chat_template=_RERANKER_SCORE_TEMPLATE,
            )
            outputs = [o.outputs.score for o in raw_outputs]

    return outputs