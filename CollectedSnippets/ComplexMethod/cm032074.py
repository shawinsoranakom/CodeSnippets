def find_main_tex_file(file_manifest, mode):
    """
    在多Tex文档中，寻找主文件，必须包含documentclass，返回找到的第一个。
    P.S. 但愿没人把latex模板放在里面传进来 (6.25 加入判定latex模板的代码)
    """
    candidates = []
    for texf in file_manifest:
        if os.path.basename(texf).startswith("merge"):
            continue
        with open(texf, "r", encoding="utf8", errors="ignore") as f:
            file_content = f.read()
        if r"\documentclass" in file_content:
            candidates.append(texf)
        else:
            continue

    if len(candidates) == 0:
        raise RuntimeError("无法找到一个主Tex文件（包含documentclass关键字）")
    elif len(candidates) == 1:
        return candidates[0]
    else:  # if len(candidates) >= 2 通过一些Latex模板中常见（但通常不会出现在正文）的单词，对不同latex源文件扣分，取评分最高者返回
        candidates_score = []
        # 给出一些判定模板文档的词作为扣分项
        unexpected_words = [
            "\\LaTeX",
            "manuscript",
            "Guidelines",
            "font",
            "citations",
            "rejected",
            "blind review",
            "reviewers",
        ]
        expected_words = ["\\input", "\\ref", "\\cite"]
        for texf in candidates:
            candidates_score.append(0)
            with open(texf, "r", encoding="utf8", errors="ignore") as f:
                file_content = f.read()
                file_content = rm_comments(file_content)
            for uw in unexpected_words:
                if uw in file_content:
                    candidates_score[-1] -= 1
            for uw in expected_words:
                if uw in file_content:
                    candidates_score[-1] += 1
        select = np.argmax(candidates_score)  # 取评分最高者返回
        return candidates[select]