def extract_paper_ids(txt):
    """从输入文本中提取多个论文ID"""
    paper_ids = []

    # 首先按换行符分割
    for line in txt.strip().split('\n'):
        line = line.strip()
        if not line:  # 跳过空行
            continue

        # 对每一行再按空格分割
        for item in line.split():
            item = item.strip()
            if not item:  # 跳过空项
                continue
            paper_info = extract_paper_id(item)
            if paper_info:
                paper_ids.append(paper_info)

    # 去除重复项，保持顺序
    unique_paper_ids = []
    seen = set()
    for paper_info in paper_ids:
        if paper_info not in seen:
            seen.add(paper_info)
            unique_paper_ids.append(paper_info)

    return unique_paper_ids