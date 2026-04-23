def download_arxiv_(url_pdf):
    if 'arxiv.org' not in url_pdf:
        if ('.' in url_pdf) and ('/' not in url_pdf):
            new_url = 'https://arxiv.org/abs/'+url_pdf
            logger.info('下载编号：', url_pdf, '自动定位：', new_url)
            # download_arxiv_(new_url)
            return download_arxiv_(new_url)
        else:
            logger.info('不能识别的URL！')
            return None
    if 'abs' in url_pdf:
        url_pdf = url_pdf.replace('abs', 'pdf')
        url_pdf = url_pdf + '.pdf'

    url_abs = url_pdf.replace('.pdf', '').replace('pdf', 'abs')
    title, other_info = get_name(_url_=url_abs)

    paper_id = title.split()[0]  # '[1712.00559]'
    if '2' in other_info['year']:
        title = other_info['year'] + ' ' + title

    known_conf = ['NeurIPS', 'NIPS', 'Nature', 'Science', 'ICLR', 'AAAI']
    for k in known_conf:
        if k in other_info['comment']:
            title = k + ' ' + title

    download_dir = get_log_folder(plugin_name='arxiv')
    os.makedirs(download_dir, exist_ok=True)

    title_str = title.replace('?', '？')\
        .replace(':', '：')\
        .replace('\"', '“')\
        .replace('\n', '')\
        .replace('  ', ' ')\
        .replace('  ', ' ')

    requests_pdf_url = url_pdf
    file_path = download_dir+title_str

    logger.info('下载中')
    proxies = get_conf('proxies')
    r = requests.get(requests_pdf_url, proxies=proxies)
    with open(file_path, 'wb+') as f:
        f.write(r.content)
    logger.info('下载完成')

    x = "%s  %s %s.bib" % (paper_id, other_info['year'], other_info['authors'])
    x = x.replace('?', '？')\
        .replace(':', '：')\
        .replace('\"', '“')\
        .replace('\n', '')\
        .replace('  ', ' ')\
        .replace('  ', ' ')
    return file_path, other_info