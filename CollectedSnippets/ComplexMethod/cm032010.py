def 解析任意code项目(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    txt_pattern = plugin_kwargs.get("advanced_arg")
    txt_pattern = txt_pattern.replace("，", ",")
    # 将要匹配的模式(例如: *.c, *.cpp, *.py, config.toml)
    pattern_include = [_.lstrip(" ,").rstrip(" ,") for _ in txt_pattern.split(",") if _ != "" and not _.strip().startswith("^")]
    if not pattern_include: pattern_include = ["*"] # 不输入即全部匹配
    # 将要忽略匹配的文件后缀(例如: ^*.c, ^*.cpp, ^*.py)
    pattern_except_suffix = [_.lstrip(" ^*.,").rstrip(" ,") for _ in txt_pattern.split(" ") if _ != "" and _.strip().startswith("^*.")]
    pattern_except_suffix += ['zip', 'rar', '7z', 'tar', 'gz'] # 避免解析压缩文件
    # 将要忽略匹配的文件名(例如: ^README.md)
    pattern_except_name = [_.lstrip(" ^*,").rstrip(" ,").replace(".", r"\.") # 移除左边通配符，移除右侧逗号，转义点号
                           for _ in txt_pattern.split(" ") # 以空格分割
                           if (_ != "" and _.strip().startswith("^") and not _.strip().startswith("^*."))   # ^开始，但不是^*.开始
                           ]
    # 生成正则表达式
    pattern_except = r'/[^/]+\.(' + "|".join(pattern_except_suffix) + ')$'
    pattern_except += '|/(' + "|".join(pattern_except_name) + ')$' if pattern_except_name != [] else ''

    history.clear()
    import glob, os, re
    if os.path.exists(txt):
        project_folder = txt
        validate_path_safety(project_folder, chatbot.get_user())
    else:
        if txt == "": txt = '空空如也的输入栏'
        report_exception(chatbot, history, a = f"解析项目: {txt}", b = f"找不到本地项目或无权访问: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return
    # 若上传压缩文件, 先寻找到解压的文件夹路径, 从而避免解析压缩文件
    maybe_dir = [f for f in glob.glob(f'{project_folder}/*') if os.path.isdir(f)]
    if len(maybe_dir)>0 and maybe_dir[0].endswith('.extract'):
        extract_folder_path = maybe_dir[0]
    else:
        extract_folder_path = project_folder
    # 按输入的匹配模式寻找上传的非压缩文件和已解压的文件
    file_manifest = [f for pattern in pattern_include for f in glob.glob(f'{extract_folder_path}/**/{pattern}', recursive=True) if "" != extract_folder_path and \
                      os.path.isfile(f) and (not re.search(pattern_except, f) or pattern.endswith('.' + re.search(pattern_except, f).group().split('.')[-1]))]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"解析项目: {txt}", b = f"找不到任何文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
        return
    yield from 解析源代码新(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)