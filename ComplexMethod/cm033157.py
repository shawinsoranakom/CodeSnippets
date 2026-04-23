def forProj(cv):
    if not cv.get("project_obj"):
        return cv

    pro_nms, desc = [], []
    for i, n in enumerate(
            sorted(cv.get("project_obj", []), key=lambda x: str(x.get("updated_at", "")) if isinstance(x, dict) else "",
                   reverse=True)):
        if n.get("name"):
            pro_nms.append(n["name"])
        if n.get("describe"):
            desc.append(str(n["describe"]))
        if n.get("responsibilities"):
            desc.append(str(n["responsibilities"]))
        if n.get("achivement"):
            desc.append(str(n["achivement"]))

    if pro_nms:
        # cv["pro_nms_tks"] = rag_tokenizer.tokenize(" ".join(pro_nms))
        cv["project_name_tks"] = rag_tokenizer.tokenize(pro_nms[0])
    if desc:
        cv["pro_desc_ltks"] = rag_tokenizer.tokenize(rmHtmlTag(" ".join(desc)))
        cv["project_desc_ltks"] = rag_tokenizer.tokenize(rmHtmlTag(desc[0]))

    return cv