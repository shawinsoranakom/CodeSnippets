def 编译Latex(chatbot, history, main_file_original, main_file_modified, work_folder_original, work_folder_modified, work_folder, mode='default'):
    import os, time
    n_fix = 1
    fixed_line = []
    max_try = 32
    chatbot.append([f"正在编译PDF文档", f'编译已经开始。当前工作路径为{work_folder}，如果程序停顿5分钟以上，请直接去该路径下取回翻译结果，或者重启之后再度尝试 ...']); yield from update_ui(chatbot=chatbot, history=history)
    chatbot.append([f"正在编译PDF文档", '...']); yield from update_ui(chatbot=chatbot, history=history); time.sleep(1); chatbot[-1] = list(chatbot[-1]) # 刷新界面
    yield from update_ui_latest_msg('编译已经开始...', chatbot, history)   # 刷新Gradio前端界面
    # 检查是否需要使用xelatex
    def check_if_need_xelatex(tex_path):
        try:
            with open(tex_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(5000)
                # 检查是否有使用xelatex的宏包
                need_xelatex = any(
                    pkg in content
                    for pkg in ['fontspec', 'xeCJK', 'xetex', 'unicode-math', 'xltxtra', 'xunicode']
                )
                if need_xelatex:
                    logger.info(f"检测到宏包需要xelatex编译, 切换至xelatex编译")
                else:
                    logger.info(f"未检测到宏包需要xelatex编译, 使用pdflatex编译")
                return need_xelatex
        except Exception:
            return False

    # 根据编译器类型返回编译命令
    def get_compile_command(compiler, filename):
        compile_command = f'{compiler} -interaction=batchmode -file-line-error {filename}.tex'
        logger.info('Latex 编译指令: ' + compile_command)
        return compile_command

    # 确定使用的编译器
    compiler = 'pdflatex'
    if check_if_need_xelatex(pj(work_folder_modified, f'{main_file_modified}.tex')):
        logger.info("检测到宏包需要xelatex编译，切换至xelatex编译")
        # Check if xelatex is installed
        try:
            import subprocess
            subprocess.run(['xelatex', '--version'], capture_output=True, check=True)
            compiler = 'xelatex'
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("检测到需要使用xelatex编译，但系统中未安装xelatex。请先安装texlive或其他提供xelatex的LaTeX发行版。")

    while True:
        import os
        may_exist_bbl = pj(work_folder_modified, f'merge.bbl')
        target_bbl = pj(work_folder_modified, f'{main_file_modified}.bbl')
        if os.path.exists(may_exist_bbl) and not os.path.exists(target_bbl):
            shutil.copyfile(may_exist_bbl, target_bbl)

        # https://stackoverflow.com/questions/738755/dont-make-me-manually-abort-a-latex-compile-when-theres-an-error
        yield from update_ui_latest_msg(f'尝试第 {n_fix}/{max_try} 次编译, 编译原始PDF ...', chatbot, history)   # 刷新Gradio前端界面
        ok = compile_latex_with_timeout(get_compile_command(compiler, main_file_original), work_folder_original)

        yield from update_ui_latest_msg(f'尝试第 {n_fix}/{max_try} 次编译, 编译转化后的PDF ...', chatbot, history)   # 刷新Gradio前端界面
        ok = compile_latex_with_timeout(get_compile_command(compiler, main_file_modified), work_folder_modified)

        if ok and os.path.exists(pj(work_folder_modified, f'{main_file_modified}.pdf')):
            # 只有第二步成功，才能继续下面的步骤
            yield from update_ui_latest_msg(f'尝试第 {n_fix}/{max_try} 次编译, 编译BibTex ...', chatbot, history)    # 刷新Gradio前端界面
            if not os.path.exists(pj(work_folder_original, f'{main_file_original}.bbl')):
                ok = compile_latex_with_timeout(f'bibtex  {main_file_original}.aux', work_folder_original)
            if not os.path.exists(pj(work_folder_modified, f'{main_file_modified}.bbl')):
                ok = compile_latex_with_timeout(f'bibtex  {main_file_modified}.aux', work_folder_modified)

            yield from update_ui_latest_msg(f'尝试第 {n_fix}/{max_try} 次编译, 编译文献交叉引用 ...', chatbot, history)  # 刷新Gradio前端界面
            ok = compile_latex_with_timeout(get_compile_command(compiler, main_file_original), work_folder_original)
            ok = compile_latex_with_timeout(get_compile_command(compiler, main_file_modified), work_folder_modified)
            ok = compile_latex_with_timeout(get_compile_command(compiler, main_file_original), work_folder_original)
            ok = compile_latex_with_timeout(get_compile_command(compiler, main_file_modified), work_folder_modified)

            if mode!='translate_zh':
                yield from update_ui_latest_msg(f'尝试第 {n_fix}/{max_try} 次编译, 使用latexdiff生成论文转化前后对比 ...', chatbot, history) # 刷新Gradio前端界面
                logger.info(    f'latexdiff --encoding=utf8 --append-safecmd=subfile {work_folder_original}/{main_file_original}.tex  {work_folder_modified}/{main_file_modified}.tex --flatten > {work_folder}/merge_diff.tex')
                ok = compile_latex_with_timeout(f'latexdiff --encoding=utf8 --append-safecmd=subfile {work_folder_original}/{main_file_original}.tex  {work_folder_modified}/{main_file_modified}.tex --flatten > {work_folder}/merge_diff.tex', os.getcwd())

                yield from update_ui_latest_msg(f'尝试第 {n_fix}/{max_try} 次编译, 正在编译对比PDF ...', chatbot, history)   # 刷新Gradio前端界面
                ok = compile_latex_with_timeout(get_compile_command(compiler, 'merge_diff'), work_folder)
                ok = compile_latex_with_timeout(f'bibtex    merge_diff.aux', work_folder)
                ok = compile_latex_with_timeout(get_compile_command(compiler, 'merge_diff'), work_folder)
                ok = compile_latex_with_timeout(get_compile_command(compiler, 'merge_diff'), work_folder)

        # <---------- 检查结果 ----------->
        results_ = ""
        original_pdf_success = os.path.exists(pj(work_folder_original, f'{main_file_original}.pdf'))
        modified_pdf_success = os.path.exists(pj(work_folder_modified, f'{main_file_modified}.pdf'))
        diff_pdf_success     = os.path.exists(pj(work_folder, f'merge_diff.pdf'))
        results_ += f"原始PDF编译是否成功: {original_pdf_success};"
        results_ += f"转化PDF编译是否成功: {modified_pdf_success};"
        results_ += f"对比PDF编译是否成功: {diff_pdf_success};"
        yield from update_ui_latest_msg(f'第{n_fix}编译结束:<br/>{results_}...', chatbot, history) # 刷新Gradio前端界面

        if diff_pdf_success:
            result_pdf = pj(work_folder_modified, f'merge_diff.pdf')    # get pdf path
            promote_file_to_downloadzone(result_pdf, rename_file=None, chatbot=chatbot)  # promote file to web UI
        if modified_pdf_success:
            yield from update_ui_latest_msg(f'转化PDF编译已经成功, 正在尝试生成对比PDF, 请稍候 ...', chatbot, history)    # 刷新Gradio前端界面
            result_pdf = pj(work_folder_modified, f'{main_file_modified}.pdf') # get pdf path
            origin_pdf = pj(work_folder_original, f'{main_file_original}.pdf') # get pdf path
            if os.path.exists(pj(work_folder, '..', 'translation')):
                shutil.copyfile(result_pdf, pj(work_folder, '..', 'translation', 'translate_zh.pdf'))
            promote_file_to_downloadzone(result_pdf, rename_file=None, chatbot=chatbot)  # promote file to web UI
            # 将两个PDF拼接
            if original_pdf_success:
                try:
                    from .latex_toolbox import merge_pdfs
                    concat_pdf = pj(work_folder_modified, f'comparison.pdf')
                    merge_pdfs(origin_pdf, result_pdf, concat_pdf)
                    if os.path.exists(pj(work_folder, '..', 'translation')):
                        shutil.copyfile(concat_pdf, pj(work_folder, '..', 'translation', 'comparison.pdf'))
                    promote_file_to_downloadzone(concat_pdf, rename_file=None, chatbot=chatbot)  # promote file to web UI
                except Exception as e:
                    logger.error(e)
                    pass
            return True # 成功啦
        else:
            if n_fix>=max_try: break
            n_fix += 1
            can_retry, main_file_modified, buggy_lines = remove_buggy_lines(
                file_path=pj(work_folder_modified, f'{main_file_modified}.tex'),
                log_path=pj(work_folder_modified, f'{main_file_modified}.log'),
                tex_name=f'{main_file_modified}.tex',
                tex_name_pure=f'{main_file_modified}',
                n_fix=n_fix,
                work_folder_modified=work_folder_modified,
                fixed_line=fixed_line
            )
            yield from update_ui_latest_msg(f'由于最为关键的转化PDF编译失败, 将根据报错信息修正tex源文件并重试, 当前报错的latex代码处于第{buggy_lines}行 ...', chatbot, history)   # 刷新Gradio前端界面
            if not can_retry: break

    return False