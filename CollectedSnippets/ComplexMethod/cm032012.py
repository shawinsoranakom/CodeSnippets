def get_files_from_everything(txt, preference=''):
    if txt == "": return False, None, None
    success = True
    if txt.startswith('http'):
        import requests
        from toolbox import get_conf
        proxies = get_conf('proxies')
        # 网络的远程文件
        if preference == 'Github':
            logger.info('正在从github下载资源 ...')
            if not txt.endswith('.md'):
                # Make a request to the GitHub API to retrieve the repository information
                url = txt.replace("https://github.com/", "https://api.github.com/repos/") + '/readme'
                response = requests.get(url, proxies=proxies)
                txt = response.json()['download_url']
            else:
                txt = txt.replace("https://github.com/", "https://raw.githubusercontent.com/")
                txt = txt.replace("/blob/", "/")

        r = requests.get(txt, proxies=proxies)
        download_local = f'{get_log_folder(plugin_name="批量Markdown翻译")}/raw-readme-{gen_time_str()}.md'
        project_folder = f'{get_log_folder(plugin_name="批量Markdown翻译")}'
        with open(download_local, 'wb+') as f: f.write(r.content)
        file_manifest = [download_local]
    elif txt.endswith('.md'):
        # 直接给定文件
        file_manifest = [txt]
        project_folder = os.path.dirname(txt)
    elif os.path.exists(txt):
        # 本地路径，递归搜索
        project_folder = txt
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.md', recursive=True)]
    else:
        project_folder = None
        file_manifest = []
        success = False

    return success, file_manifest, project_folder