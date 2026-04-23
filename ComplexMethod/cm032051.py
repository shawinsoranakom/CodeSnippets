def 图片生成_NanoBanana(prompt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 清空历史,以免输入溢出

    if prompt.strip() == "":
        chatbot.append((prompt, "[Local Message] 图像生成提示为空白"))
        yield from update_ui(chatbot=chatbot, history=history)
        return
    chatbot.append((
        prompt,
        "正在调用 NanoBanana 图像生成, 正在处理中 ....."
    ))

    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面 由于请求gpt需要一段时间,我们先及时地做一次界面更新
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")

    model = "nano-banana"
    resolution = plugin_kwargs["resolution"]
    aspectRatio = plugin_kwargs["aspect ratio"]

    # Validate aspect ratio
    valid_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2", "4:5", "5:4", "21:9"]
    if aspectRatio not in valid_ratios:
        aspectRatio = "1:1"

    try:
        # get image from recent upload
        has_recent_image_upload, image_paths = have_any_recent_upload_image_files(chatbot, pop=True)
        if has_recent_image_upload:
            _, image_base64_array = make_multimodal_input(prompt, image_paths)
        else:
            _, image_base64_array = prompt, []

        # get image from session storage
        if 'session_file_storage' in chatbot._cookies:
            try:
                image_base64_array += [base64.b64encode(open(chatbot._cookies['session_file_storage'], 'rb').read()).decode('utf-8')]
            except:
                logger.exception("Failed to read session_file_storage and parse to image base64.")

        # only keep last image if any
        if len(image_base64_array) > 1:
            image_base64_array = [image_base64_array[-1]]

        # Generate image
        _, image_path = yield from gen_image_banana(chatbot, history, prompt, image_base64_list=image_base64_array, resolution=resolution, aspectRatio=aspectRatio, model=model)

        # Build response message
        response_msg = f'模型: {model}<br/>分辨率: {resolution}<br/>比例: {aspectRatio}<br/><br/>'
        response_msg += f'本地文件地址: <br/>`{image_path}`<br/>'
        response_msg += f'本地文件预览: <br/><div align="center"><img src="file={image_path}"></div>'

        # register image
        chatbot._cookies['session_file_storage'] = image_path

        yield from update_ui_latest_msg(lastmsg=response_msg, chatbot=chatbot, history=history, delay=0)

    except Exception as e:
        chatbot.append([prompt, f'生成图像失败: {str(e)}'])

    yield from update_ui(chatbot=chatbot, history=history)