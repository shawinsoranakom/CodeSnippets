def __init__(
        self,
        image_parsing_strategy: Literal["llm"] | None = None,
        table_parsing_strategy: Literal["docling", "llm"] | None = "docling",
        multimodal_llm: llms.OpenAIChat | llms.LiteLLMChat | None = None,
        cache_strategy: udfs.CacheStrategy | None = None,
        pdf_pipeline_options: dict = {},
        chunk: bool = True,
        *,
        async_mode: Literal["batch_async", "fully_async"] = "batch_async",
    ):
        with optional_imports("xpack-llm-docs"):
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                TableStructureOptions,
            )
            from docling.document_converter import (
                DocumentConverter,
                InputFormat,
                PdfFormatOption,
            )

        from pathway.xpacks.llm import _parser_utils

        self.chunker: _parser_utils._HybridChunker | None = None
        self.multimodal_llm: llms.OpenAIChat | llms.LiteLLMChat | None = None

        if image_parsing_strategy == "llm" or table_parsing_strategy == "llm":
            if multimodal_llm is None:
                warnings.warn(
                    "`image_parsing_strategy` is set to `llm`, but `multimodal_llm` is "
                    f"not specified in DoclingParser, defaulting to `{DEFAULT_VISION_MODEL}`."
                )
                self.multimodal_llm = llms.OpenAIChat(
                    model=DEFAULT_VISION_MODEL,
                    cache_strategy=udfs.DefaultCache(),
                    retry_strategy=udfs.ExponentialBackoffRetryStrategy(max_retries=4),
                    verbose=True,
                )
            else:
                self.multimodal_llm = multimodal_llm
        else:
            self.multimodal_llm = None

        self.image_parsing_strategy = image_parsing_strategy
        self.table_parsing_strategy = table_parsing_strategy

        default_table_structure_options = {
            # whether to perform cell matching; small impact on speed, noticeable impact on quality
            "do_cell_matching": True,
            # mode of table parsing; either `fast` or `accurate`; big impact on speed
            # small impact on quality (might be useful for complex tables though)
            "mode": "fast",
        }
        default_pipeline_options = {
            # whether to parse tables or not; big impact on speed
            "do_table_structure": (
                True if table_parsing_strategy == "docling" else False
            ),
            # whether to make images of pages; small impact on speed
            "generate_page_images": True if self.multimodal_llm is not None else False,
            # whether to make images of pictures; small impact on speed
            "generate_picture_images": (
                True if self.multimodal_llm is not None else False
            ),
            "generate_table_images": (
                True if self.multimodal_llm is not None else False
            ),
            # whether to perform OCR; big impact on speed
            "do_ocr": False,
            # scale of images; small impact on speed
            "images_scale": 2,
        }

        pipeline_options = PdfPipelineOptions(
            **(default_pipeline_options | pdf_pipeline_options)
        )
        pipeline_options.table_structure_options = TableStructureOptions(
            **(
                default_table_structure_options
                | pdf_pipeline_options.get("table_structure_options", {})
            )
        )

        # actual docling converter
        self.converter: DocumentConverter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            },
            # TODO: Add more file types
        )

        # modified Docling's chunker
        if chunk:
            self.chunker = _parser_utils._HybridChunker(merge_peers=True)

        executor = _prepare_executor(async_mode=async_mode)
        super().__init__(cache_strategy=cache_strategy, executor=executor)