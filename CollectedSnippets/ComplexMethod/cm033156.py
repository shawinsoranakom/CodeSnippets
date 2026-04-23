def forEdu(cv):
    if not cv.get("education_obj"):
        cv["integerity_flt"] *= 0.8
        return cv

    first_fea, fea, maj, fmaj, deg, fdeg, sch, fsch, st_dt, ed_dt = [], [], [], [], [], [], [], [], [], []
    edu_nst = []
    edu_end_dt = ""
    cv["school_rank_int"] = 1000000
    for ii, n in enumerate(sorted(cv["education_obj"], key=lambda x: x.get("start_time", "3"))):
        e = {}
        if n.get("end_time"):
            if n["end_time"] > edu_end_dt:
                edu_end_dt = n["end_time"]
            try:
                dt = n["end_time"]
                if re.match(r"[0-9]{9,}", dt):
                    dt = turnTm2Dt(dt)
                y, m, d = getYMD(dt)
                ed_dt.append(str(y))
                e["end_dt_kwd"] = str(y)
            except Exception as e:
                pass
        if n.get("start_time"):
            try:
                dt = n["start_time"]
                if re.match(r"[0-9]{9,}", dt):
                    dt = turnTm2Dt(dt)
                y, m, d = getYMD(dt)
                st_dt.append(str(y))
                e["start_dt_kwd"] = str(y)
            except Exception:
                pass

        r = schools.select(n.get("school_name", ""))
        if r:
            if str(r.get("type", "")) == "1":
                fea.append("211")
            if str(r.get("type", "")) == "2":
                fea.append("211")
            if str(r.get("is_abroad", "")) == "1":
                fea.append("留学")
            if str(r.get("is_double_first", "")) == "1":
                fea.append("双一流")
            if str(r.get("is_985", "")) == "1":
                fea.append("985")
            if str(r.get("is_world_known", "")) == "1":
                fea.append("海外知名")
            if r.get("rank") and cv["school_rank_int"] > r["rank"]:
                cv["school_rank_int"] = r["rank"]

        if n.get("school_name") and isinstance(n["school_name"], str):
            sch.append(re.sub(r"(211|985|重点大学|[,&;；-])", "", n["school_name"]))
            e["sch_nm_kwd"] = sch[-1]
        fea.append(rag_tokenizer.fine_grained_tokenize(rag_tokenizer.tokenize(n.get("school_name", ""))).split()[-1])

        if n.get("discipline_name") and isinstance(n["discipline_name"], str):
            maj.append(n["discipline_name"])
            e["major_kwd"] = n["discipline_name"]

        if not n.get("degree") and "985" in fea and not first_fea:
            n["degree"] = "1"

        if n.get("degree"):
            d = degrees.get_name(n["degree"])
            if d:
                e["degree_kwd"] = d
            if d == "本科" and ("专科" in deg or "专升本" in deg or "中专" in deg or "大专" in deg or re.search(r"(成人|自考|自学考试)", n.get("school_name",""))):
                d = "专升本"
            if d:
                deg.append(d)

            # for first degree
            if not fdeg and d in ["中专", "专升本", "专科", "本科", "大专"]:
                fdeg = [d]
                if n.get("school_name"):
                    fsch = [n["school_name"]]
                if n.get("discipline_name"):
                    fmaj = [n["discipline_name"]]
                first_fea = copy.deepcopy(fea)

        edu_nst.append(e)

    cv["sch_rank_kwd"] = []
    if cv["school_rank_int"] <= 20 or ("海外名校" in fea and cv["school_rank_int"] <= 200):
        cv["sch_rank_kwd"].append("顶尖学校")
    elif 50 >= cv["school_rank_int"] > 20 or ("海外名校" in fea and 500 >= cv["school_rank_int"] > 200):
        cv["sch_rank_kwd"].append("精英学校")
    elif cv["school_rank_int"] > 50 and ("985" in fea or "211" in fea) or ("海外名校" in fea and cv["school_rank_int"] > 500):
        cv["sch_rank_kwd"].append("优质学校")
    else:
        cv["sch_rank_kwd"].append("一般学校")

    if edu_nst:
        cv["edu_nst"] = edu_nst
    if fea:
        cv["edu_fea_kwd"] = list(set(fea))
    if first_fea:
        cv["edu_first_fea_kwd"] = list(set(first_fea))
    if maj:
        cv["major_kwd"] = maj
    if fsch:
        cv["first_school_name_kwd"] = fsch
    if fdeg:
        cv["first_degree_kwd"] = fdeg
    if fmaj:
        cv["first_major_kwd"] = fmaj
    if st_dt:
        cv["edu_start_kwd"] = st_dt
    if ed_dt:
        cv["edu_end_kwd"] = ed_dt
    if ed_dt:
        cv["edu_end_int"] = max([int(t) for t in ed_dt])
    if deg:
        if "本科" in deg and "专科" in deg:
            deg.append("专升本")
            deg = [d for d in deg if d != '本科']
        cv["degree_kwd"] = deg
        cv["highest_degree_kwd"] = highest_degree(deg)
    if edu_end_dt:
        try:
            if re.match(r"[0-9]{9,}", edu_end_dt):
                edu_end_dt = turnTm2Dt(edu_end_dt)
            if edu_end_dt.strip("\n") == "至今":
                edu_end_dt = cv.get("updated_at_dt", str(datetime.date.today()))
            y, m, d = getYMD(edu_end_dt)
            cv["work_exp_flt"] = min(int(str(datetime.date.today())[0:4]) - int(y), cv.get("work_exp_flt", 1000))
        except Exception as e:
            logging.exception("forEdu {} {} {}".format(e, edu_end_dt, cv.get("work_exp_flt")))
    if sch:
        cv["school_name_kwd"] = sch
        if (len(cv.get("degree_kwd", [])) >= 1 and "本科" in cv["degree_kwd"]) \
                or all([c.lower() in ["硕士", "博士", "mba", "博士后"] for c in cv.get("degree_kwd", [])]) \
                or not cv.get("degree_kwd"):
            for c in sch:
                if schools.is_good(c):
                    if "tag_kwd" not in cv:
                        cv["tag_kwd"] = []
                    cv["tag_kwd"].append("好学校")
                    cv["tag_kwd"].append("好学历")
                    break
        if (len(cv.get("degree_kwd", [])) >= 1 and "本科" in cv["degree_kwd"] and
            any([d.lower() in ["硕士", "博士", "mba", "博士"] for d in cv.get("degree_kwd", [])])) \
                or all([d.lower() in ["硕士", "博士", "mba", "博士后"] for d in cv.get("degree_kwd", [])]) \
                or any([d in ["mba", "emba", "博士后"] for d in cv.get("degree_kwd", [])]):
            if "tag_kwd" not in cv:
                cv["tag_kwd"] = []
            if "好学历" not in cv["tag_kwd"]:
                cv["tag_kwd"].append("好学历")

    if cv.get("major_kwd"):
        cv["major_tks"] = rag_tokenizer.tokenize(" ".join(maj))
    if cv.get("school_name_kwd"):
        cv["school_name_tks"] = rag_tokenizer.tokenize(" ".join(sch))
    if cv.get("first_school_name_kwd"):
        cv["first_school_name_tks"] = rag_tokenizer.tokenize(" ".join(fsch))
    if cv.get("first_major_kwd"):
        cv["first_major_tks"] = rag_tokenizer.tokenize(" ".join(fmaj))

    return cv