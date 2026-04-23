def Latex精细分解与转化(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, mode='proofread', switch_prompt=None, opts=[]):
    import time, os, re
    from ..crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency
    from .latex_actions import LatexPaperFileGroup, LatexPaperSplit

    #  <-------- 寻找主tex文件 ---------->
    maintex = find_main_tex_file(file_manifest, mode)
    chatbot.append((f"定位主Latex文件", f'[Local Message] 分析结果：该项目的Latex主文件是{maintex}, 如果分析错误, 请立即终止程序, 删除或修改歧义文件, 然后重试。主程序即将开始, 请稍候。'))
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
    time.sleep(3)

    #  <-------- 读取Latex文件, 将多文件tex工程融合为一个巨型tex ---------->
    main_tex_basename = os.path.basename(maintex)
    assert main_tex_basename.endswith('.tex')
    main_tex_basename_bare = main_tex_basename[:-4]
    may_exist_bbl = pj(project_folder, f'{main_tex_basename_bare}.bbl')
    if os.path.exists(may_exist_bbl):
        shutil.copyfile(may_exist_bbl, pj(project_folder, f'merge.bbl'))
        shutil.copyfile(may_exist_bbl, pj(project_folder, f'merge_{mode}.bbl'))
        shutil.copyfile(may_exist_bbl, pj(project_folder, f'merge_diff.bbl'))

    with open(maintex, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        merged_content = merge_tex_files(project_folder, content, mode)

    with open(project_folder + '/merge.tex', 'w', encoding='utf-8', errors='replace') as f:
        f.write(merged_content)

    #  <-------- 精细切分latex文件 ---------->
    chatbot.append((f"Latex文件融合完成", f'[Local Message] 正在精细切分latex文件，这需要一段时间计算，文档越长耗时越长，请耐心等待。'))
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面
    lps = LatexPaperSplit()
    lps.read_title_and_abstract(merged_content)
    res = lps.split(merged_content, project_folder, opts) # 消耗时间的函数
    #  <-------- 拆分过长的latex片段 ---------->
    pfg = LatexPaperFileGroup()
    for index, r in enumerate(res):
        pfg.file_paths.append('segment-' + str(index))
        pfg.file_contents.append(r)

    pfg.run_file_split(max_token_limit=1024)
    n_split = len(pfg.sp_file_contents)

    #  <-------- 根据需要切换prompt ---------->
    inputs_array, sys_prompt_array = switch_prompt(pfg, mode)
    inputs_show_user_array = [f"{mode} {f}" for f in pfg.sp_file_tag]

    if os.path.exists(pj(project_folder,'temp.pkl')):

        #  <-------- 【仅调试】如果存在调试缓存文件，则跳过GPT请求环节 ---------->
        pfg = objload(file=pj(project_folder,'temp.pkl'))

    else:
        #  <-------- gpt 多线程请求 ---------->
        history_array = [[""] for _ in range(n_split)]
        # LATEX_EXPERIMENTAL, = get_conf('LATEX_EXPERIMENTAL')
        # if LATEX_EXPERIMENTAL:
        #     paper_meta = f"The paper you processing is `{lps.title}`, a part of the abstraction is `{lps.abstract}`"
        #     paper_meta_max_len = 888
        #     history_array = [[ paper_meta[:paper_meta_max_len] + '...',  "Understand, what should I do?"] for _ in range(n_split)]

        gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs_array=inputs_array,
            inputs_show_user_array=inputs_show_user_array,
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=history_array,
            sys_prompt_array=sys_prompt_array,
            # max_workers=5,  # 并行任务数量限制, 最多同时执行5个, 其他的排队等待
            scroller_max_len = 40
        )

        #  <-------- 文本碎片重组为完整的tex片段 ---------->
        pfg.sp_file_result = []
        for i_say, gpt_say, orig_content in zip(gpt_response_collection[0::2], gpt_response_collection[1::2], pfg.sp_file_contents):
            pfg.sp_file_result.append(gpt_say)
        pfg.merge_result()

        # <-------- 临时存储用于调试 ---------->
        pfg.get_token_num = None
        objdump(pfg, file=pj(project_folder,'temp.pkl'))

    write_html(pfg.sp_file_contents, pfg.sp_file_result, chatbot=chatbot, project_folder=project_folder)

    #  <-------- 写出文件 ---------->
    model_name = llm_kwargs['llm_model'].replace('_', '\\_')  # 替换LLM模型名称中的下划线为转义字符
    msg = f"当前大语言模型: {model_name}，当前语言模型温度设定: {llm_kwargs['temperature']}。"
    final_tex = lps.merge_result(pfg.file_result, mode, msg)
    objdump((lps, pfg.file_result, mode, msg), file=pj(project_folder,'merge_result.pkl'))

    with open(project_folder + f'/merge_{mode}.tex', 'w', encoding='utf-8', errors='replace') as f:
        if mode != 'translate_zh' or "binary" in final_tex: f.write(final_tex)


    #  <-------- 整理结果, 退出 ---------->
    chatbot.append((f"完成了吗？", 'GPT结果已输出, 即将编译PDF'))
    yield from update_ui(chatbot=chatbot, history=history) # 刷新界面

    #  <-------- 返回 ---------->
    return project_folder + f'/merge_{mode}.tex'