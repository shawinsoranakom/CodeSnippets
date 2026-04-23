def __init__(
        self,
        config: PreTrainedConfig | None = None,
        question_encoder: PreTrainedModel | None = None,
        generator: PreTrainedModel | None = None,
        retriever: RagRetriever | None = None,  # or maybe just use a `set_retriever(...)` method
        **kwargs,
    ):
        r"""
        question_encoder (`PreTrainedModel`, *optional*):
            The model responsible for encoding the question into hidden states for retrieval.
        generator (`PreTrainedModel`, *optional*):
            The model responsible for generating text based on retrieved documents.
        retriever (`RagRetriever`, *optional*):
            The component responsible for retrieving documents from a knowledge base given the encoded question.
        """
        assert config is not None or (question_encoder is not None and generator is not None), (
            "Either a configuration or an question_encoder and a generator has to be provided."
        )

        if config is None:
            config = RagConfig.from_question_encoder_generator_configs(
                question_encoder.config, generator.config, **kwargs
            )
        else:
            assert isinstance(config, self.config_class), f"config: {config} has to be of type {self.config_class}"
        super().__init__(config)
        if question_encoder is None:
            from ..auto.modeling_auto import AutoModel

            question_encoder = AutoModel.from_config(config.question_encoder)

        if generator is None:
            from ..auto.modeling_auto import AutoModelForSeq2SeqLM

            generator = AutoModelForSeq2SeqLM.from_config(config.generator)

        self.retriever = retriever
        if self.retriever is not None:
            assert isinstance(retriever, RagRetriever), (
                f"`self.retriever` is of type {type(self.retriever)}, but should be of type `RagRetriever`"
            )
            self.retriever = retriever

        self.question_encoder = question_encoder
        self.generator = generator

        self.ctx_encoder = None
        self.context_encoder_training = False

        self.post_init()