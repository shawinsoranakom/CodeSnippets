def upload_to_gptac_cloud_if_user_allow(chatbot, arxiv_id):
    try:
        # 如果用户允许，我们将arxiv论文PDF上传到GPTAC学术云
        from toolbox import map_file_to_sha256
        # 检查是否顺利，如果没有生成预期的文件，则跳过
        is_result_good = False
        for file_path in chatbot._cookies.get("files_to_promote", []):
            if file_path.endswith('translate_zh.pdf'):
                is_result_good = True
        if not is_result_good:
            return
        # 上传文件
        for file_path in chatbot._cookies.get("files_to_promote", []):
            align_name = None
            # normalized name
            for name in ['translate_zh.pdf', 'comparison.pdf']:
                if file_path.endswith(name): align_name = name
            # if match any align name
            if align_name:
                logger.info(f'Uploading to GPTAC cloud as the user has set `allow_cloud_io`: {file_path}')
                with open(file_path, 'rb') as f:
                    import requests
                    url = 'https://cloud-2.agent-matrix.com/arxiv_tf_paper_normal_upload'
                    files = {'file': (align_name, f, 'application/octet-stream')}
                    data = {
                        'arxiv_id': arxiv_id,
                        'file_hash': map_file_to_sha256(file_path),
                        'language': 'zh',
                        'trans_prompt': 'to_be_implemented',
                        'llm_model': 'to_be_implemented',
                        'llm_model_param': 'to_be_implemented',
                    }
                    resp = requests.post(url=url, files=files, data=data, timeout=30)
                logger.info(f'Uploading terminate ({resp.status_code})`: {file_path}')
    except:
        # 如果上传失败，不会中断程序，因为这是次要功能
        pass