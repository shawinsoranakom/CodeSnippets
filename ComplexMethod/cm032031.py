def arxiv_download(chatbot, history, txt, allow_cache=True):
    def check_cached_translation_pdf(arxiv_id):
        translation_dir = pj(ARXIV_CACHE_DIR, arxiv_id, 'translation')
        if not os.path.exists(translation_dir):
            os.makedirs(translation_dir)
        target_file = pj(translation_dir, 'translate_zh.pdf')
        if os.path.exists(target_file):
            promote_file_to_downloadzone(target_file, rename_file=None, chatbot=chatbot)
            target_file_compare = pj(translation_dir, 'comparison.pdf')
            if os.path.exists(target_file_compare):
                promote_file_to_downloadzone(target_file_compare, rename_file=None, chatbot=chatbot)
            return target_file
        return False

    def is_float(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    if txt.startswith('https://arxiv.org/pdf/'):
        arxiv_id = txt.split('/')[-1]   # 2402.14207v2.pdf
        txt = arxiv_id.split('v')[0]  # 2402.14207

    if ('.' in txt) and ('/' not in txt) and is_float(txt):  # is arxiv ID
        txt = 'https://arxiv.org/abs/' + txt.strip()
    if ('.' in txt) and ('/' not in txt) and is_float(txt[:10]):  # is arxiv ID
        txt = 'https://arxiv.org/abs/' + txt[:10]

    if not txt.startswith('https://arxiv.org'):
        return txt, None    # 是本地文件，跳过下载

    # <-------------- inspect format ------------->
    chatbot.append([f"检测到arxiv文档连接", '尝试下载 ...'])
    yield from update_ui(chatbot=chatbot, history=history)
    time.sleep(1)  # 刷新界面

    url_ = txt  # https://arxiv.org/abs/1707.06690

    if not txt.startswith('https://arxiv.org/abs/'):
        msg = f"解析arxiv网址失败, 期望格式例如: https://arxiv.org/abs/1707.06690。实际得到格式: {url_}。"
        yield from update_ui_latest_msg(msg, chatbot=chatbot, history=history)  # 刷新界面
        return msg, None
    # <-------------- set format ------------->
    arxiv_id = url_.split('/abs/')[-1]
    if 'v' in arxiv_id: arxiv_id = arxiv_id[:10]
    cached_translation_pdf = check_cached_translation_pdf(arxiv_id)
    if cached_translation_pdf and allow_cache: return cached_translation_pdf, arxiv_id

    extract_dst = pj(ARXIV_CACHE_DIR, arxiv_id, 'extract')
    translation_dir = pj(ARXIV_CACHE_DIR, arxiv_id, 'e-print')
    dst = pj(translation_dir, arxiv_id + '.tar')
    os.makedirs(translation_dir, exist_ok=True)
    # <-------------- download arxiv source file ------------->

    def fix_url_and_download():
        # for url_tar in [url_.replace('/abs/', '/e-print/'), url_.replace('/abs/', '/src/')]:
        for url_tar in [url_.replace('/abs/', '/src/'), url_.replace('/abs/', '/e-print/')]:
            proxies = get_conf('proxies')
            r = requests.get(url_tar, proxies=proxies)
            if r.status_code == 200:
                with open(dst, 'wb+') as f:
                    f.write(r.content)
                return True
        return False

    if os.path.exists(dst) and allow_cache:
        yield from update_ui_latest_msg(f"调用缓存 {arxiv_id}", chatbot=chatbot, history=history)  # 刷新界面
        success = True
    else:
        yield from update_ui_latest_msg(f"开始下载 {arxiv_id}", chatbot=chatbot, history=history)  # 刷新界面
        success = fix_url_and_download()
        yield from update_ui_latest_msg(f"下载完成 {arxiv_id}", chatbot=chatbot, history=history)  # 刷新界面


    if not success:
        yield from update_ui_latest_msg(f"下载失败 {arxiv_id}", chatbot=chatbot, history=history)
        raise tarfile.ReadError(f"论文下载失败 {arxiv_id}")

    # <-------------- extract file ------------->
    from toolbox import extract_archive
    try:
        extract_archive(file_path=dst, dest_dir=extract_dst)
    except tarfile.ReadError:
        os.remove(dst)
        raise tarfile.ReadError(f"论文下载失败")
    return extract_dst, arxiv_id