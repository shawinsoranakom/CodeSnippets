def zhihu_download_playlist(url, output_dir='.', merge=True, info_only=False, **kwargs):
    if "question" not in url or "answer" in url:  # question page
        raise TypeError("URL does not conform to specifications, Support question only."
                        " Example URL: https://www.zhihu.com/question/267782048")
    url = url.split("?")[0]
    if url[-1] == "/":
        question_id = url.split("/")[-2]
    else:
        question_id = url.split("/")[-1]
    videos_url = r"https://www.zhihu.com/api/v4/questions/{}/answers".format(question_id)
    try:
        questions = json.loads(get_content(videos_url))
    except json.decoder.JSONDecodeError:
        raise TypeError("Check whether the problem URL exists.Example URL: https://www.zhihu.com/question/267782048")

    count = 0
    while 1:
        for data in questions["data"]:
            kwargs["zhihu_offset"] = count
            zhihu_download("https://www.zhihu.com/question/{}/answer/{}".format(question_id, data["id"]),
                           output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)
            count += 1
        if questions["paging"]["is_end"]:
            return
        questions = json.loads(get_content(questions["paging"]["next"], headers=fake_headers))