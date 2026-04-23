def from_llamaindex_components(  # type: ignore
        cls,
        *docs,
        transformations: list["llama_index.core.schema.TransformComponent"],
        parser: Callable[[bytes], list[tuple[str, dict]]] | None = None,
        **kwargs,
    ):
        """
        Initializes VectorStoreServer by using LlamaIndex TransformComponents.
        Args:
            docs: pathway tables typically coming out of connectors which contain source documents
            transformations: list of LlamaIndex components. The last component in this list
                is required to inherit from LlamaIndex `BaseEmbedding`
            parser: callable that parses file contents into a list of documents
        """
        try:
            from llama_index.core.base.embeddings.base import BaseEmbedding
            from llama_index.core.ingestion.pipeline import run_transformations
            from llama_index.core.schema import BaseNode, MetadataMode, TextNode
        except ImportError:
            raise ImportError(
                "Please install llama-index-core: `pip install llama-index-core`"
            )
        try:
            from llama_index.legacy.embeddings.base import (
                BaseEmbedding as LegacyBaseEmbedding,
            )

            legacy_llama_index_not_imported = True
        except ImportError:
            legacy_llama_index_not_imported = False

        def node_transformer(x: str) -> list[BaseNode]:
            return [TextNode(text=x)]

        def node_to_pathway(x: Sequence[BaseNode]) -> list[tuple[str, dict]]:
            return [
                (node.get_content(metadata_mode=MetadataMode.NONE), node.extra_info)
                for node in x
            ]

        if transformations is None or not transformations:
            raise ValueError("Transformations list cannot be None or empty.")

        if not isinstance(transformations[-1], BaseEmbedding) and (
            legacy_llama_index_not_imported
            or not isinstance(transformations[-1], LegacyBaseEmbedding)
        ):
            raise ValueError(
                f"Last step of transformations should be an instance of {BaseEmbedding.__name__}, "
                f"found {type(transformations[-1])}."
            )

        embedder = cast(BaseEmbedding, transformations.pop())

        @pw.udf
        async def embedding_callable(x: str) -> np.ndarray:
            embedding = await embedder.aget_text_embedding(x)
            return np.array(embedding)

        def generic_transformer(x: str) -> list[tuple[str, dict]]:
            starting_node = node_transformer(x)
            final_node = run_transformations(starting_node, transformations)
            return node_to_pathway(final_node)

        return VectorStoreServer(
            *docs,
            embedder=embedding_callable,
            parser=parser,
            splitter=generic_transformer,
            **kwargs,
        )