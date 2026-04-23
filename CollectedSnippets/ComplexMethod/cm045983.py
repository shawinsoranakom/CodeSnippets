async def aio_do_parse(
        output_dir,
        pdf_file_names: list[str],
        pdf_bytes_list: list[bytes],
        p_lang_list: list[str],
        backend="pipeline",
        parse_method="auto",
        formula_enable=True,
        table_enable=True,
        server_url=None,
        f_draw_layout_bbox=True,
        f_draw_span_bbox=True,
        f_dump_md=True,
        f_dump_middle_json=True,
        f_dump_model_output=True,
        f_dump_orig_pdf=True,
        f_dump_content_list=True,
        f_make_md_mode=MakeMode.MM_MD,
        start_page_id=0,
        end_page_id=None,
        **kwargs,
):
    need_remove_index = _process_office_doc(
        output_dir,
        pdf_file_names=pdf_file_names,
        pdf_bytes_list=pdf_bytes_list,
        f_dump_md=f_dump_md,
        f_dump_middle_json=f_dump_middle_json,
        f_dump_model_output=f_dump_model_output,
        f_dump_orig_file=f_dump_orig_pdf,
        f_dump_content_list=f_dump_content_list,
        f_make_md_mode=f_make_md_mode,
    )
    for index in sorted(need_remove_index, reverse=True):
        del pdf_bytes_list[index]
        del pdf_file_names[index]
        del p_lang_list[index]
    if not pdf_bytes_list:
        logger.warning("No valid PDF or image files to process.")
        return

    # 预处理PDF字节数据
    pdf_bytes_list = _prepare_pdf_bytes(pdf_bytes_list, start_page_id, end_page_id)

    if backend == "pipeline":
        # pipeline模式暂不支持异步，使用同步处理方式
        _process_pipeline(
            output_dir, pdf_file_names, pdf_bytes_list, p_lang_list,
            parse_method, formula_enable, table_enable,
            f_draw_layout_bbox, f_draw_span_bbox, f_dump_md, f_dump_middle_json,
            f_dump_model_output, f_dump_orig_pdf, f_dump_content_list, f_make_md_mode
        )
    else:
        if backend.startswith("vlm-"):
            backend = backend[4:]

            if backend == "vllm-engine":
                raise Exception("vlm-vllm-engine backend is not supported in async mode, please use vlm-vllm-async-engine backend")

            if backend == "auto-engine":
                backend = get_vlm_engine(inference_engine='auto', is_async=True)

            os.environ['MINERU_VLM_FORMULA_ENABLE'] = str(formula_enable)
            os.environ['MINERU_VLM_TABLE_ENABLE'] = str(table_enable)

            await _async_process_vlm(
                output_dir, pdf_file_names, pdf_bytes_list, backend,
                f_draw_layout_bbox, f_draw_span_bbox, f_dump_md, f_dump_middle_json,
                f_dump_model_output, f_dump_orig_pdf, f_dump_content_list, f_make_md_mode,
                server_url, **kwargs,
            )
        elif backend.startswith("hybrid-"):
            ensure_backend_dependencies(backend)
            backend = backend[7:]

            if backend == "vllm-engine":
                raise Exception("hybrid-vllm-engine backend is not supported in async mode, please use hybrid-vllm-async-engine backend")

            if backend == "auto-engine":
                backend = get_vlm_engine(inference_engine='auto', is_async=True)

            os.environ['MINERU_VLM_TABLE_ENABLE'] = str(table_enable)
            os.environ['MINERU_VLM_FORMULA_ENABLE'] = "true"

            await _async_process_hybrid(
                output_dir, pdf_file_names, pdf_bytes_list, p_lang_list, parse_method, formula_enable, backend,
                f_draw_layout_bbox, f_draw_span_bbox, f_dump_md, f_dump_middle_json,
                f_dump_model_output, f_dump_orig_pdf, f_dump_content_list, f_make_md_mode,
                server_url, **kwargs,
            )