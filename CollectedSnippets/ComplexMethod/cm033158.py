def forWork(cv):
    if not cv.get("work_obj"):
        cv["integerity_flt"] *= 0.7
        return cv

    flds = ["position_name", "corporation_name", "corporation_id", "responsibilities",
            "industry_name", "subordinates_count"]
    duas = []
    scales = []
    fea = {c: [] for c in flds}
    latest_job_tm = ""
    goodcorp = False
    goodcorp_ = False
    work_st_tm = ""
    corp_tags = []
    for i, n in enumerate(
            sorted(cv.get("work_obj", []), key=lambda x: str(x.get("start_time", "")) if isinstance(x, dict) else "",
                   reverse=True)):
        if isinstance(n, str):
            try:
                n = json_loads(n)
            except Exception:
                continue

        if n.get("start_time") and (not work_st_tm or n["start_time"] < work_st_tm):
            work_st_tm = n["start_time"]
        for c in flds:
            if not n.get(c) or str(n[c]) == '0':
                fea[c].append("")
                continue
            if c == "corporation_name":
                n[c] = corporations.corpNorm(n[c], False)
                if corporations.is_good(n[c]):
                    if i == 0:
                        goodcorp = True
                    else:
                        goodcorp_ = True
                ct = corporations.corp_tag(n[c])
                if i == 0:
                    corp_tags.extend(ct)
                elif ct and ct[0] != "软外":
                    corp_tags.extend([f"{t}(曾)" for t in ct])

            fea[c].append(rmHtmlTag(str(n[c]).lower()))

        y, m, d = getYMD(n.get("start_time"))
        if not y or not m:
            continue
        st = "%s-%02d-%02d" % (y, int(m), int(d))
        latest_job_tm = st

        y, m, d = getYMD(n.get("end_time"))
        if (not y or not m) and i > 0:
            continue
        if not y or not m or int(y) > 2022:
            y, m, d = getYMD(str(n.get("updated_at", "")))
        if not y or not m:
            continue
        ed = "%s-%02d-%02d" % (y, int(m), int(d))

        try:
            duas.append((datetime.datetime.strptime(ed, "%Y-%m-%d") - datetime.datetime.strptime(st, "%Y-%m-%d")).days)
        except Exception:
            logging.exception("forWork {} {}".format(n.get("start_time"), n.get("end_time")))

        if n.get("scale"):
            r = re.search(r"^([0-9]+)", str(n["scale"]))
            if r:
                scales.append(int(r.group(1)))

    if goodcorp:
        if "tag_kwd" not in cv:
            cv["tag_kwd"] = []
        cv["tag_kwd"].append("好公司")
    if goodcorp_:
        if "tag_kwd" not in cv:
            cv["tag_kwd"] = []
        cv["tag_kwd"].append("好公司(曾)")

    if corp_tags:
        if "tag_kwd" not in cv:
            cv["tag_kwd"] = []
        cv["tag_kwd"].extend(corp_tags)
        cv["corp_tag_kwd"] = [c for c in corp_tags if re.match(r"(综合|行业)", c)]

    if latest_job_tm:
        cv["latest_job_dt"] = latest_job_tm
    if fea["corporation_id"]:
        cv["corporation_id"] = fea["corporation_id"]

    if fea["position_name"]:
        cv["position_name_tks"] = rag_tokenizer.tokenize(fea["position_name"][0])
        cv["position_name_sm_tks"] = rag_tokenizer.fine_grained_tokenize(cv["position_name_tks"])
        cv["pos_nm_tks"] = rag_tokenizer.tokenize(" ".join(fea["position_name"][1:]))

    if fea["industry_name"]:
        cv["industry_name_tks"] = rag_tokenizer.tokenize(fea["industry_name"][0])
        cv["industry_name_sm_tks"] = rag_tokenizer.fine_grained_tokenize(cv["industry_name_tks"])
        cv["indu_nm_tks"] = rag_tokenizer.tokenize(" ".join(fea["industry_name"][1:]))

    if fea["corporation_name"]:
        cv["corporation_name_kwd"] = fea["corporation_name"][0]
        cv["corp_nm_kwd"] = fea["corporation_name"]
        cv["corporation_name_tks"] = rag_tokenizer.tokenize(fea["corporation_name"][0])
        cv["corporation_name_sm_tks"] = rag_tokenizer.fine_grained_tokenize(cv["corporation_name_tks"])
        cv["corp_nm_tks"] = rag_tokenizer.tokenize(" ".join(fea["corporation_name"][1:]))

    if fea["responsibilities"]:
        cv["responsibilities_ltks"] = rag_tokenizer.tokenize(fea["responsibilities"][0])
        cv["resp_ltks"] = rag_tokenizer.tokenize(" ".join(fea["responsibilities"][1:]))

    if fea["subordinates_count"]:
        fea["subordinates_count"] = [int(i) for i in fea["subordinates_count"] if
                                                               re.match(r"[^0-9]+$", str(i))]
    if fea["subordinates_count"]:
        cv["max_sub_cnt_int"] = np.max(fea["subordinates_count"])

    if isinstance(cv.get("corporation_id"), int):
        cv["corporation_id"] = [str(cv["corporation_id"])]
    if not cv.get("corporation_id"):
        cv["corporation_id"] = []
    for i in cv.get("corporation_id", []):
        cv["baike_flt"] = max(corporations.baike(i), cv["baike_flt"] if "baike_flt" in cv else 0)

    if work_st_tm:
        try:
            if re.match(r"[0-9]{9,}", work_st_tm):
                work_st_tm = turnTm2Dt(work_st_tm)
            y, m, d = getYMD(work_st_tm)
            cv["work_exp_flt"] = min(int(str(datetime.date.today())[0:4]) - int(y), cv.get("work_exp_flt", 1000))
        except Exception as e:
            logging.exception("forWork {} {} {}".format(e, work_st_tm, cv.get("work_exp_flt")))

    cv["job_num_int"] = 0
    if duas:
        cv["dua_flt"] = np.mean(duas)
        cv["cur_dua_int"] = duas[0]
        cv["job_num_int"] = len(duas)
    if scales:
        cv["scale_flt"] = np.max(scales)
    return cv