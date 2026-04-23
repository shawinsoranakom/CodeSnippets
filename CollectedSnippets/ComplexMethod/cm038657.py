def init_pooling_io_processors(
    supported_tasks: tuple[SupportedTask, ...],
    vllm_config: VllmConfig,
    renderer: BaseRenderer,
    chat_template_config: ChatTemplateConfig,
) -> dict[str, PoolingIOProcessor]:
    model_config = vllm_config.model_config
    processors: dict[str, type[PoolingIOProcessor]] = {}
    pooling_task = model_config.get_pooling_task(supported_tasks)

    if pooling_task == "classify":
        from .classify.io_processor import ClassifyIOProcessor

        processors["classify"] = ClassifyIOProcessor

    if pooling_task == "token_classify":
        from .classify.io_processor import TokenClassifyIOProcessor

        processors["token_classify"] = TokenClassifyIOProcessor

    if pooling_task == "embed":
        from .embed.io_processor import EmbedIOProcessor

        processors["embed"] = EmbedIOProcessor

    if pooling_task == "token_embed":
        from .embed.io_processor import TokenEmbedIOProcessor

        processors["token_embed"] = TokenEmbedIOProcessor

    if has_io_processor(
        vllm_config,
        model_config.io_processor_plugin,
    ):
        from .pooling.io_processor import PluginWithIOProcessorPlugins

        processors["plugin"] = PluginWithIOProcessorPlugins
    elif pooling_task == "plugin":
        from .pooling.io_processor import PluginWithoutIOProcessorPlugins

        processors["plugin"] = PluginWithoutIOProcessorPlugins

    if enable_scoring_api(supported_tasks, model_config):
        from .scoring.io_processor import ScoringIOProcessors

        score_type: str | None = SCORE_TYPE_MAP.get(pooling_task, None)  # type: ignore[arg-type]
        if score_type is not None and score_type in ScoringIOProcessors:
            processors[score_type] = ScoringIOProcessors[score_type]

    if model_config.architecture == "JinaForRanking":
        from .embed.io_processor import JinaRankingTokenEmbedIOProcessor
        from .scoring.io_processor import ScoringIOProcessors

        processors["token_embed"] = JinaRankingTokenEmbedIOProcessor
        processors["late-interaction"] = ScoringIOProcessors["jina-reranking-scoring"]

    return {
        task: processor_cls(
            vllm_config=vllm_config,
            renderer=renderer,
            chat_template_config=chat_template_config,
        )
        for task, processor_cls in processors.items()
    }