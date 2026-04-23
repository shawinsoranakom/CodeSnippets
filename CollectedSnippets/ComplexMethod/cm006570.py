def test_constants_imports(self):
        """Test that constants from langchain are accessible."""
        from lfx.field_typing import (
            AgentExecutor,
            BaseChatMemory,
            BaseChatModel,
            BaseDocumentCompressor,
            BaseLanguageModel,
            BaseLLM,
            BaseLoader,
            BaseMemory,
            BaseOutputParser,
            BasePromptTemplate,
            BaseRetriever,
            Chain,
            ChatPromptTemplate,
            Document,
            Embeddings,
            PromptTemplate,
            TextSplitter,
            Tool,
            VectorStore,
        )

        # Verify they are not None (actual types or stubs)
        assert AgentExecutor is not None
        assert BaseChatMemory is not None
        assert BaseChatModel is not None
        assert BaseDocumentCompressor is not None
        assert BaseLanguageModel is not None
        assert BaseLLM is not None
        assert BaseLoader is not None
        assert BaseMemory is not None
        assert BaseOutputParser is not None
        assert BasePromptTemplate is not None
        assert BaseRetriever is not None
        assert Chain is not None
        assert ChatPromptTemplate is not None
        assert Document is not None
        assert Embeddings is not None
        assert PromptTemplate is not None
        assert TextSplitter is not None
        assert Tool is not None
        assert VectorStore is not None