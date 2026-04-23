def vision_figure_parser_pdf_wrapper(tbls, callback=None, **kwargs):
    if not tbls:
        return []
    sections = kwargs.get("sections")
    parser_config = kwargs.get("parser_config", {})
    context_size = max(0, int(parser_config.get("image_context_size", 0) or 0))
    try:
        vision_model_config = get_tenant_default_model_by_type(kwargs["tenant_id"], LLMType.IMAGE2TEXT)
        vision_model = LLMBundle(kwargs["tenant_id"], vision_model_config)
        callback(0.7, "Visual model detected. Attempting to enhance figure extraction...")
    except Exception:
        vision_model = None
    if vision_model:

        def is_figure_item(item):
            return is_image_like(item[0][0]) and isinstance(item[0][1], list)

        figures_data = [item for item in tbls if is_figure_item(item)]
        figure_contexts = []
        if sections and figures_data and context_size > 0:
            figure_contexts = append_context2table_image4pdf(
                sections,
                figures_data,
                context_size,
                return_context=True,
            )
        try:
            docx_vision_parser = VisionFigureParser(
                vision_model=vision_model,
                figures_data=figures_data,
                figure_contexts=figure_contexts,
                context_size=context_size,
                **kwargs,
            )
            boosted_figures = docx_vision_parser(callback=callback)
            tbls = [item for item in tbls if not is_figure_item(item)]
            tbls.extend(boosted_figures)
        except Exception as e:
            callback(0.8, f"Visual model error: {e}. Skipping figure parsing enhancement.")
    return tbls