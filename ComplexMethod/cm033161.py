def corpNorm(nm, add_region=True):
    global CORP_TKS
    if not nm or not isinstance(nm, str):
        return ""
    nm = rag_tokenizer.tradi2simp(rag_tokenizer.strQ2B(nm)).lower()
    nm = re.sub(r"&amp;", "&", nm)
    nm = re.sub(r"[\(\)（）\+'\"\t \*\\【】-]+", " ", nm)
    nm = re.sub(
        r"([—-]+.*| +co\..*|corp\..*| +inc\..*| +ltd.*)", "", nm, count=10000, flags=re.IGNORECASE
    )
    nm = re.sub(
        r"(计算机|技术|(技术|科技|网络)*有限公司|公司|有限|研发中心|中国|总部)$",
        "",
        nm,
        count=10000,
        flags=re.IGNORECASE,
    )
    if not nm or (len(nm) < 5 and not regions.isName(nm[0:2])):
        return nm

    tks = rag_tokenizer.tokenize(nm).split()
    reg = [t for i, t in enumerate(tks) if regions.isName(t) and (t != "中国" or i > 0)]
    nm = ""
    for t in tks:
        if regions.isName(t) or t in CORP_TKS:
            continue
        if re.match(r"[0-9a-zA-Z\\,.]+", t) and re.match(r".*[0-9a-zA-Z\,.]+$", nm):
            nm += " "
        nm += t

    r = re.search(r"^([^a-z0-9 \(\)&]{2,})[a-z ]{4,}$", nm.strip())
    if r:
        nm = r.group(1)
    r = re.search(r"^([a-z ]{3,})[^a-z0-9 \(\)&]{2,}$", nm.strip())
    if r:
        nm = r.group(1)
    return nm.strip() + (("" if not reg else "(%s)" % reg[0]) if add_region else "")