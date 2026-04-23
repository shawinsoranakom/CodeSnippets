def main(ctx,
        example_enable,
        http_client_enable,
        api_enable, max_convert_pages,
        server_name, server_port, api_url, enable_vlm_preload, latex_delimiters_type, **kwargs
):

    # 创建 i18n 实例，支持中英文
    i18n = gr.I18n(
        en={
            "upload_file": "Please select a file to upload (PDF, image, DOCX, PPTX, or XLSX)",
            "max_pages": "Max convert pages",
            "backend": "Backend",
            "server_url": "Server URL",
            "server_url_info": "OpenAI-compatible server URL for http-client backend.",
            "recognition_options": "**Recognition Options:**",
            "table_enable": "Enable table recognition",
            "table_info": "If disabled, tables will be shown as images.",
            "formula_label_vlm": "Enable display formula recognition",
            "formula_label_pipeline": "Enable formula recognition",
            "formula_label_hybrid": "Enable inline formula recognition",
            "formula_info_vlm": "If disabled, display formulas will be shown as images.",
            "formula_info_pipeline": "If disabled, display formulas will be shown as images, and inline formulas will not be detected or parsed.",
            "formula_info_hybrid": "If disabled, inline formulas will not be detected or parsed.",
            "ocr_language": "OCR Language",
            "ocr_language_info": "Select the OCR language for image-based PDFs and images.",
            "force_ocr": "Force enable OCR",
            "force_ocr_info": "Enable only if the result is extremely poor. Requires correct OCR language.",
            "convert": "Convert",
            "clear": "Clear",
            "doc_preview": "Document preview",
            "examples": "Examples:",
            "convert_status": "Conversion Status",
            "convert_result": "Convert result",
            "md_rendering": "Markdown rendering",
            "md_text": "Markdown text",
            "backend_info_vlm": "High-precision parsing via VLM, supports Chinese and English documents only.",
            "backend_info_pipeline": "Traditional Multi-model pipeline parsing, supports multiple languages, hallucination-free.",
            "backend_info_hybrid": "High-precision hybrid parsing, supports multiple languages.",
            "backend_info_default": "Select the backend engine for document parsing.",
        },
        zh={
            "upload_file": "请选择要上传的文件（PDF、图片、DOCX、PPTX 或 XLSX）",
            "max_pages": "最大转换页数",
            "backend": "解析后端",
            "server_url": "服务器地址",
            "server_url_info": "http-client 后端的 OpenAI 兼容服务器地址。",
            "recognition_options": "**识别选项：**",
            "table_enable": "启用表格识别",
            "table_info": "禁用后，表格将显示为图片。",
            "formula_label_vlm": "启用行间公式识别",
            "formula_label_pipeline": "启用公式识别",
            "formula_label_hybrid": "启用行内公式识别",
            "formula_info_vlm": "禁用后，行间公式将显示为图片。",
            "formula_info_pipeline": "禁用后，行间公式将显示为图片，行内公式将不会被检测或解析。",
            "formula_info_hybrid": "禁用后，行内公式将不会被检测或解析。",
            "ocr_language": "OCR 语言",
            "ocr_language_info": "为扫描版 PDF 和图片选择 OCR 语言。",
            "force_ocr": "强制启用 OCR",
            "force_ocr_info": "仅在识别效果极差时启用，需选择正确的 OCR 语言。",
            "convert": "转换",
            "clear": "清除",
            "doc_preview": "文档预览",
            "examples": "示例：",
            "convert_status": "转换状态",
            "convert_result": "转换结果",
            "md_rendering": "Markdown 渲染",
            "md_text": "Markdown 文本",
            "backend_info_vlm": "多模态大模型高精度解析，仅支持中英文文档。",
            "backend_info_pipeline": "传统多模型管道解析，支持多语言，无幻觉。",
            "backend_info_hybrid": "高精度混合解析，支持多语言。",
            "backend_info_default": "选择文档解析的后端引擎。",
        },
    )

    # 根据后端类型获取公式识别标签（闭包函数以支持 i18n）
    def get_formula_label(backend_choice):
        if backend_choice.startswith("vlm"):
            return i18n("formula_label_vlm")
        elif backend_choice == "pipeline":
            return i18n("formula_label_pipeline")
        elif backend_choice.startswith("hybrid"):
            return i18n("formula_label_hybrid")
        else:
            return i18n("formula_label_pipeline")

    def get_formula_info(backend_choice):
        if backend_choice.startswith("vlm"):
            return i18n("formula_info_vlm")
        elif backend_choice == "pipeline":
            return i18n("formula_info_pipeline")
        elif backend_choice.startswith("hybrid"):
            return i18n("formula_info_hybrid")
        else:
            return ""

    def get_backend_info(backend_choice):
        if backend_choice.startswith("vlm"):
            return i18n("backend_info_vlm")
        elif backend_choice == "pipeline":
            return i18n("backend_info_pipeline")
        elif backend_choice.startswith("hybrid"):
            return i18n("backend_info_hybrid")
        else:
            return i18n("backend_info_default")

    # 更新界面函数
    def update_interface(backend_choice):
        formula_label_update = gr.update(label=get_formula_label(backend_choice), info=get_formula_info(backend_choice))
        backend_info_update = gr.update(info=get_backend_info(backend_choice))
        if "http-client" in backend_choice:
            client_options_update = gr.update(visible=True)
        else:
            client_options_update = gr.update(visible=False)
        if "vlm" in backend_choice:
            ocr_options_update = gr.update(visible=False)
        else:
            ocr_options_update = gr.update(visible=True)

        return client_options_update, ocr_options_update, formula_label_update, backend_info_update


    del kwargs
    _gradio_local_api_server.configure(
        resolve_gradio_local_api_cli_args(
            ctx.args,
            api_url=api_url,
            enable_vlm_preload=enable_vlm_preload,
        )
    )

    if latex_delimiters_type == 'a':
        latex_delimiters = latex_delimiters_type_a
    elif latex_delimiters_type == 'b':
        latex_delimiters = latex_delimiters_type_b
    elif latex_delimiters_type == 'all':
        latex_delimiters = latex_delimiters_type_all
    else:
        raise ValueError(f"Invalid latex delimiters type: {latex_delimiters_type}.")


    async def convert_to_markdown_stream(
        file_path,
        end_pages=10,
        is_ocr=False,
        formula_enable=True,
        table_enable=True,
        language="ch",
        backend="pipeline",
        url=None,
    ):
        async for update in stream_to_markdown(
            file_path=file_path,
            end_pages=end_pages,
            is_ocr=is_ocr,
            formula_enable=formula_enable,
            table_enable=table_enable,
            language=language,
            backend=backend,
            url=url,
            api_url=api_url,
        ):
            yield update

    suffixes = [f".{suffix}" for suffix in pdf_suffixes + image_suffixes + office_suffixes]
    with gr.Blocks() as demo:
        gr.HTML(header)
        with gr.Row():
            with gr.Column(variant='panel', scale=5):
                with gr.Row():
                    input_file = gr.File(label=i18n("upload_file"), file_types=suffixes)
                # 下面这些选项在上传 office 文件时会被自动隐藏
                with gr.Group() as options_group:
                    with gr.Row():
                        max_pages = gr.Slider(1, max_convert_pages, max_convert_pages, step=1, label=i18n("max_pages"))
                    with gr.Row():
                        drop_list = ["pipeline", "vlm-auto-engine", "hybrid-auto-engine"]
                        preferred_option = "hybrid-auto-engine"
                        if http_client_enable:
                            drop_list.extend(["vlm-http-client", "hybrid-http-client"])
                        backend = gr.Dropdown(drop_list, label=i18n("backend"), value=preferred_option, info=get_backend_info(preferred_option))
                    with gr.Row(visible=False) as client_options:
                        url = gr.Textbox(label=i18n("server_url"), value='http://localhost:30000', placeholder='http://localhost:30000', info=i18n("server_url_info"))
                    with gr.Row(equal_height=True):
                        with gr.Column():
                            gr.Markdown(i18n("recognition_options"))
                            table_enable = gr.Checkbox(label=i18n("table_enable"), value=True, info=i18n("table_info"))
                            formula_enable = gr.Checkbox(label=get_formula_label(preferred_option), value=True, info=get_formula_info(preferred_option))
                        with gr.Column() as ocr_options:
                            language = gr.Dropdown(all_lang, label=i18n("ocr_language"), value='ch (Chinese, English, Chinese Traditional)', info=i18n("ocr_language_info"))
                            is_ocr = gr.Checkbox(label=i18n("force_ocr"), value=False, info=i18n("force_ocr_info"))
                with gr.Row():
                    change_bu = gr.Button(i18n("convert"))
                    clear_bu = gr.ClearButton(value=i18n("clear"))
                _doc_preview_label = "doc preview" if IS_GRADIO_6 else i18n("doc_preview")
                doc_show = PDF(label=_doc_preview_label, interactive=False, visible=True, height=800)
                office_html = gr.HTML(value="", visible=False)
                if example_enable:
                    example_root = os.path.join(os.getcwd(), 'examples')
                    if os.path.exists(example_root):
                        gr.Examples(
                            label=i18n("examples"),
                            examples=[os.path.join(example_root, _) for _ in os.listdir(example_root) if
                                      _.endswith(tuple(suffixes))],
                            inputs=input_file
                        )

            with gr.Column(variant='panel', scale=5):
                status_box = gr.TextArea(
                    label=i18n("convert_status"),
                    value="",
                    lines=4,
                    max_lines=4,
                    interactive=False,
                    autoscroll=True,
                    elem_classes=["convert-status-box"],
                )
                output_file = gr.File(label=i18n("convert_result"), interactive=False)
                with gr.Blocks():
                    with gr.Tab(i18n("md_rendering")):
                        _md_copy_kwargs = {"buttons": ["copy"]} if IS_GRADIO_6 else {"show_copy_button": True}
                        md = gr.Markdown(
                            label=i18n("md_rendering"),
                            height=1200,
                            latex_delimiters=latex_delimiters,
                            line_breaks=True,
                            **_md_copy_kwargs
                        )
                    with gr.Tab(i18n("md_text")):
                        _textarea_copy_kwargs = {"buttons": ["copy"]} if IS_GRADIO_6 else {"show_copy_button": True}
                        md_text = gr.TextArea(
                            lines=45,
                            label=i18n("md_text"),
                            **_textarea_copy_kwargs
                        )

        # 添加事件处理
        _private_api_kwargs = (
            {"api_visibility": "private", "queue": False}
            if IS_GRADIO_6
            else {"api_name": False, "queue": False}
        )
        backend.change(
            fn=update_interface,
            inputs=[backend],
            outputs=[client_options, ocr_options, formula_enable, backend],
            **_private_api_kwargs
        )
        # 添加demo.load事件，在页面加载时触发一次界面更新
        demo.load(
            fn=update_interface,
            inputs=[backend],
            outputs=[client_options, ocr_options, formula_enable, backend],
            **_private_api_kwargs
        )
        status_box.change(
            fn=None,
            inputs=[status_box],
            outputs=[],
            js=STATUS_BOX_AUTOSCROLL_JS,
            **_private_api_kwargs
        )
        clear_bu.add([input_file, md, doc_show, md_text, output_file, is_ocr, office_html, status_box])

        # 清除按钮额外重置 UI 可见性（ClearButton 不一定触发 input_file.change）
        clear_bu.click(
            fn=lambda: (
                gr.update(visible=True),
                gr.update(value=None, visible=True),
                gr.update(value="", visible=False),
                gr.update(value=""),
            ),
            inputs=[],
            outputs=[options_group, doc_show, office_html, status_box],
            **_private_api_kwargs
        )

        # 第一阶段：快速更新 options_group 和 office_html，不涉及 gradio_pdf 组件
        # 第二阶段（.then）：单独更新 doc_show，使 office_html 的 processing 遮罩
        # 在第一阶段完成后立即消失，规避 gradio_pdf 0.0.24 与 Gradio 6 的兼容性问题。
        input_file.change(
            fn=update_file_options_html,
            inputs=input_file,
            outputs=[options_group, office_html],
            **_private_api_kwargs
        ).then(
            fn=update_doc_show,
            inputs=input_file,
            outputs=[doc_show],
            **_private_api_kwargs
        )
        _to_md_api_kwargs = (
            {
                "api_visibility": "public" if api_enable else "private",
                "queue": True,
                "show_progress": "hidden",
            }
            if IS_GRADIO_6
            else {
                "api_name": "to_markdown" if api_enable else False,
                "queue": True,
                "show_progress": "hidden",
            }
        )
        change_bu.click(
            fn=convert_to_markdown_stream,
            inputs=[input_file, max_pages, is_ocr, formula_enable, table_enable, language, backend, url],
            outputs=[status_box, output_file, md, md_text, doc_show],
            **_to_md_api_kwargs
        )

    demo.queue(default_concurrency_limit=None)

    if IS_GRADIO_6:
        footer_links = ["gradio", "settings"]
        if api_enable:
            footer_links.append("api")
        _launch_kwargs = {"footer_links": footer_links}
    else:
        _launch_kwargs = {"show_api": api_enable}
    maybe_prepare_local_api_for_gradio_startup(
        api_url=api_url,
        enable_vlm_preload=enable_vlm_preload,
    )
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        i18n=i18n,
        **_launch_kwargs,
    )