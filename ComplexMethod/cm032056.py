def get_meta_information(url, chatbot, history):
    import arxiv
    import difflib
    import re
    from bs4 import BeautifulSoup
    from toolbox import get_conf
    from urllib.parse import urlparse
    session = requests.session()

    proxies = get_conf('proxies')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Cache-Control':'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Connection': 'keep-alive'
    }
    try:
        session.proxies.update(proxies)
    except:
        report_exception(chatbot, history,
                    a=f"获取代理失败 无代理状态下很可能无法访问OpenAI家族的模型及谷歌学术 建议：检查USE_PROXY选项是否修改。",
                    b=f"尝试直接连接")
        yield from update_ui(chatbot=chatbot, history=history)  # 刷新界面
    session.headers.update(headers)

    response = session.get(url)
    # 解析网页内容
    soup = BeautifulSoup(response.text, "html.parser")

    def string_similar(s1, s2):
        return difflib.SequenceMatcher(None, s1, s2).quick_ratio()

    if ENABLE_ALL_VERSION_SEARCH:
        def search_all_version(url):
            time.sleep(random.randint(1,5)) # 睡一会防止触发google反爬虫
            response = session.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            for result in soup.select(".gs_ri"):
                try:
                    url = result.select_one(".gs_rt").a['href']
                except:
                    continue
                arxiv_id = extract_arxiv_id(url)
                if not arxiv_id:
                    continue
                search = arxiv.Search(
                    id_list=[arxiv_id],
                    max_results=1,
                    sort_by=arxiv.SortCriterion.Relevance,
                )
                try: paper = next(search.results())
                except: paper = None
                return paper

            return None

        def extract_arxiv_id(url):
            # 返回给定的url解析出的arxiv_id，如url未成功匹配返回None
            pattern = r'arxiv.org/abs/([^/]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            else:
                return None

    profile = []
    # 获取所有文章的标题和作者
    for result in soup.select(".gs_ri"):
        title = result.a.text.replace('\n', ' ').replace('  ', ' ')
        author = result.select_one(".gs_a").text
        try:
            citation = result.select_one(".gs_fl > a[href*='cites']").text  # 引用次数是链接中的文本，直接取出来
        except:
            citation = 'cited by 0'
        abstract = result.select_one(".gs_rs").text.strip()  # 摘要在 .gs_rs 中的文本，需要清除首尾空格

        # 首先在arxiv上搜索，获取文章摘要
        search = arxiv.Search(
            query = title,
            max_results = 1,
            sort_by = arxiv.SortCriterion.Relevance,
        )
        try: paper = next(search.results())
        except: paper = None

        is_match = paper is not None and string_similar(title, paper.title) > 0.90

        # 如果在Arxiv上匹配失败，检索文章的历史版本的题目
        if not is_match and ENABLE_ALL_VERSION_SEARCH:
            other_versions_page_url = [tag['href'] for tag in result.select_one('.gs_flb').select('.gs_nph') if 'cluster' in tag['href']]
            if len(other_versions_page_url) > 0:
                other_versions_page_url = other_versions_page_url[0]
                paper = search_all_version('http://' + urlparse(url).netloc + other_versions_page_url)
                is_match = paper is not None and string_similar(title, paper.title) > 0.90

        if is_match:
            # same paper
            abstract = paper.summary.replace('\n', ' ')
            is_paper_in_arxiv = True
        else:
            # different paper
            abstract = abstract
            is_paper_in_arxiv = False

        logging.info('[title]:' + title)
        logging.info('[author]:' + author)
        logging.info('[citation]:' + citation)

        profile.append({
            'title': title,
            'author': author,
            'citation': citation,
            'abstract': abstract,
            'is_paper_in_arxiv': is_paper_in_arxiv,
        })

        chatbot[-1] = [chatbot[-1][0], title + f'\n\n是否在arxiv中（不在arxiv中无法获取完整摘要）:{is_paper_in_arxiv}\n\n' + abstract]
        yield from update_ui(chatbot=chatbot, history=[]) # 刷新界面
    return profile