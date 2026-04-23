def write_chat_to_file_legacy(chatbot, history=None, file_name=None):
    """
    将对话记录history以Markdown格式写入文件中。如果没有指定文件名，则使用当前时间生成文件名。
    """
    import os
    import time
    from themes.theme import advanced_css

    if (file_name is not None) and (file_name != "") and (not file_name.endswith('.html')): file_name += '.html'
    else: file_name = None

    if file_name is None:
        file_name = f_prefix + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.html'
    fp = os.path.join(get_log_folder(get_user(chatbot), plugin_name='chat_history'), file_name)

    with open(fp, 'w', encoding='utf8') as f:
        from textwrap import dedent
        form = dedent("""
        <!DOCTYPE html><head><meta charset="utf-8"><title>对话存档</title><style>{CSS}</style></head>
        <body>
        <div class="test_temp1" style="width:10%; height: 500px; float:left;"></div>
        <div class="test_temp2" style="width:80%;padding: 40px;float:left;padding-left: 20px;padding-right: 20px;box-shadow: rgba(0, 0, 0, 0.2) 0px 0px 8px 8px;border-radius: 10px;">
            <div class="chat-body" style="display: flex;justify-content: center;flex-direction: column;align-items: center;flex-wrap: nowrap;">
                {CHAT_PREVIEW}
                <div></div>
                <div></div>
                <div style="text-align: center;width:80%;padding: 0px;float:left;padding-left:20px;padding-right:20px;box-shadow: rgba(0, 0, 0, 0.05) 0px 0px 1px 2px;border-radius: 1px;">对话（原始数据）</div>
                {HISTORY_PREVIEW}
            </div>
        </div>
        <div class="test_temp3" style="width:10%; height: 500px; float:left;"></div>
        </body>
        """)

        qa_from = dedent("""
        <div class="QaBox" style="width:80%;padding: 20px;margin-bottom: 20px;box-shadow: rgb(0 255 159 / 50%) 0px 0px 1px 2px;border-radius: 4px;">
            <div class="Question" style="border-radius: 2px;">{QUESTION}</div>
            <hr color="blue" style="border-top: dotted 2px #ccc;">
            <div class="Answer" style="border-radius: 2px;">{ANSWER}</div>
        </div>
        """)

        history_from = dedent("""
        <div class="historyBox" style="width:80%;padding: 0px;float:left;padding-left:20px;padding-right:20px;box-shadow: rgba(0, 0, 0, 0.05) 0px 0px 1px 2px;border-radius: 1px;">
            <div class="entry" style="border-radius: 2px;">{ENTRY}</div>
        </div>
        """)
        CHAT_PREVIEW_BUF = ""
        for i, contents in enumerate(chatbot):
            question, answer = contents[0], contents[1]
            if question is None: question = ""
            try: question = str(question)
            except: question = ""
            if answer is None: answer = ""
            try: answer = str(answer)
            except: answer = ""
            CHAT_PREVIEW_BUF += qa_from.format(QUESTION=question, ANSWER=answer)

        HISTORY_PREVIEW_BUF = ""
        for h in history:
            HISTORY_PREVIEW_BUF += history_from.format(ENTRY=h)
        html_content = form.format(CHAT_PREVIEW=CHAT_PREVIEW_BUF, HISTORY_PREVIEW=HISTORY_PREVIEW_BUF, CSS=advanced_css)
        f.write(html_content)

    promote_file_to_downloadzone(fp, rename_file=file_name, chatbot=chatbot)
    return '对话历史写入：' + fp