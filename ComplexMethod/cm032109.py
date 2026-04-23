def 解析PDF_DOC2X(pdf_file_path, format="tex"):
    """
    format: 'tex', 'md', 'docx'
    """

    DOC2X_API_KEY = get_conf("DOC2X_API_KEY")
    latex_dir = get_log_folder(plugin_name="pdf_ocr_latex")
    markdown_dir = get_log_folder(plugin_name="pdf_ocr")
    doc2x_api_key = DOC2X_API_KEY

    # < ------ 第1步：预上传获取URL，然后上传文件 ------ >
    logger.info("Doc2x 上传文件：预上传获取URL")
    res = make_request(
        "POST",
        "https://v2.doc2x.noedgeai.com/api/v2/parse/preupload",
        headers={"Authorization": "Bearer " + doc2x_api_key},
        timeout=15,
    )
    res_data = doc2x_api_response_status(res)
    upload_url = res_data["url"]
    uuid = res_data["uid"]

    logger.info("Doc2x 上传文件：上传文件")
    with open(pdf_file_path, "rb") as file:
        res = make_request("PUT", upload_url, data=file, timeout=60)
    res.raise_for_status()

    # < ------ 第2步：轮询等待 ------ >
    logger.info("Doc2x 处理文件中：轮询等待")
    params = {"uid": uuid}
    max_attempts = 60
    attempt = 0
    while attempt < max_attempts:
        res = make_request(
            "GET",
            "https://v2.doc2x.noedgeai.com/api/v2/parse/status",
            headers={"Authorization": "Bearer " + doc2x_api_key},
            params=params,
            timeout=15,
        )
        res_data = doc2x_api_response_status(res)
        if res_data["status"] == "success":
            break
        elif res_data["status"] == "processing":
            time.sleep(5)
            logger.info(f"Doc2x is processing at {res_data['progress']}%")
            attempt += 1
        else:
            raise RuntimeError(f"Doc2x return an error: {res_data}")
    if attempt >= max_attempts:
        raise RuntimeError("Doc2x processing timeout after maximum attempts")

    # < ------ 第3步：提交转化 ------ >
    logger.info("Doc2x 第3步：提交转化")
    data = {
        "uid": uuid,
        "to": format,
        "formula_mode": "dollar",
        "filename": "output"
    }
    res = make_request(
        "POST",
        "https://v2.doc2x.noedgeai.com/api/v2/convert/parse",
        headers={"Authorization": "Bearer " + doc2x_api_key},
        json=data,
        timeout=15,
    )
    doc2x_api_response_status(res, uid=f"uid: {uuid}")

    # < ------ 第4步：等待结果 ------ >
    logger.info("Doc2x 第4步：等待结果")
    params = {"uid": uuid}
    max_attempts = 36
    attempt = 0
    while attempt < max_attempts:
        res = make_request(
            "GET",
            "https://v2.doc2x.noedgeai.com/api/v2/convert/parse/result",
            headers={"Authorization": "Bearer " + doc2x_api_key},
            params=params,
            timeout=15,
        )
        res_data = doc2x_api_response_status(res, uid=f"uid: {uuid}")
        if res_data["status"] == "success":
            break
        elif res_data["status"] == "processing":
            time.sleep(3)
            logger.info("Doc2x still processing to convert file")
            attempt += 1
    if attempt >= max_attempts:
        raise RuntimeError("Doc2x conversion timeout after maximum attempts")

    # < ------ 第5步：最后的处理 ------ >
    logger.info("Doc2x 第5步：下载转换后的文件")

    if format == "tex":
        target_path = latex_dir
    if format == "md":
        target_path = markdown_dir
    os.makedirs(target_path, exist_ok=True)

    max_attempt = 3
    # < ------ 下载 ------ >
    for attempt in range(max_attempt):
        try:
            result_url = res_data["url"]
            res = make_request("GET", result_url, timeout=60)
            zip_path = os.path.join(target_path, gen_time_str() + ".zip")
            unzip_path = os.path.join(target_path, gen_time_str())
            if res.status_code == 200:
                with open(zip_path, "wb") as f:
                    f.write(res.content)
            else:
                raise RuntimeError(f"Doc2x return an error: {res.json()}")
        except Exception as e:
            if attempt < max_attempt - 1:
                logger.error(f"Failed to download uid = {uuid} file, retrying... {e}")
                time.sleep(3)
                continue
            else:
                raise e

    # < ------ 解压 ------ >
    import zipfile
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(unzip_path)
    return zip_path, unzip_path