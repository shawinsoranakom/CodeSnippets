def parse(cv):
    for k in cv.keys():
        if cv[k] == '\\N':
            cv[k] = ''
    # cv = cv.asDict()
    tks_fld = ["address", "corporation_name", "discipline_name", "email", "expect_city_names",
               "expect_industry_name", "expect_position_name", "industry_name", "industry_names", "name",
               "position_name", "school_name", "self_remark", "title_name"]
    small_tks_fld = ["corporation_name", "expect_position_name", "position_name", "school_name", "title_name"]
    kwd_fld = ["address", "city", "corporation_type", "degree", "discipline_name", "expect_city_names", "email",
               "expect_industry_name", "expect_position_name", "expect_type", "gender", "industry_name",
               "industry_names", "political_status", "position_name", "scale", "school_name", "phone", "tel"]
    num_fld = ["annual_salary", "annual_salary_from", "annual_salary_to", "expect_annual_salary", "expect_salary_from",
               "expect_salary_to", "salary_month"]

    is_fld = [
        ("is_fertility", "已育", "未育"),
        ("is_house", "有房", "没房"),
        ("is_management_experience", "有管理经验", "无管理经验"),
        ("is_marital", "已婚", "未婚"),
        ("is_oversea", "有海外经验", "无海外经验")
    ]

    rmkeys = []
    for k in cv.keys():
        if cv[k] is None:
            rmkeys.append(k)
        if (isinstance(cv[k], list) or isinstance(cv[k], str)) and len(cv[k]) == 0:
            rmkeys.append(k)
    for k in rmkeys:
        del cv[k]

    integrity = 0.
    flds_num = 0.

    def hasValues(flds):
        nonlocal integrity, flds_num
        flds_num += len(flds)
        for f in flds:
            v = str(cv.get(f, ""))
            if len(v) > 0 and v != '0' and v != '[]':
                integrity += 1

    hasValues(tks_fld)
    hasValues(small_tks_fld)
    hasValues(kwd_fld)
    hasValues(num_fld)
    cv["integerity_flt"] = integrity / flds_num

    if cv.get("corporation_type"):
        for p, r in [(r"(公司|企业|其它|其他|Others*|\n|未填写|Enterprises|Company|companies)", ""),
                     (r"[／/．·　<\(（]+.*", ""),
                     (r".*(合资|民企|股份制|中外|私营|个体|Private|创业|Owned|投资).*", "民营"),
                     (r".*(机关|事业).*", "机关"),
                     (r".*(非盈利|Non-profit).*", "非盈利"),
                     (r".*(外企|外商|欧美|foreign|Institution|Australia|港资).*", "外企"),
                     (r".*国有.*", "国企"),
                     (r"[ （）\(\)人/·0-9-]+", ""),
                     (r".*(元|规模|于|=|北京|上海|至今|中国|工资|州|shanghai|强|餐饮|融资|职).*", "")]:
            cv["corporation_type"] = re.sub(p, r, cv["corporation_type"], count=1000, flags=re.IGNORECASE)
        if len(cv["corporation_type"]) < 2:
            del cv["corporation_type"]

    if cv.get("political_status"):
        for p, r in [
            (r".*党员.*", "党员"),
            (r".*(无党派|公民).*", "群众"),
            (r".*团员.*", "团员")]:
            cv["political_status"] = re.sub(p, r, cv["political_status"])
        if not re.search(r"[党团群]", cv["political_status"]):
            del cv["political_status"]

    if cv.get("phone"):
        cv["phone"] = re.sub(r"^0*86([0-9]{11})", r"\1", re.sub(r"[^0-9]+", "", cv["phone"]))

    keys = list(cv.keys())
    for k in keys:
        # deal with json objects
        if k.find("_obj") > 0:
            try:
                cv[k] = json_loads(cv[k])
                cv[k] = [a for _, a in cv[k].items()]
                nms = []
                for n in cv[k]:
                    if not isinstance(n, dict) or "name" not in n or not n.get("name"):
                        continue
                    n["name"] = re.sub(r"(（442）|\t )", "", n["name"]).strip().lower()
                    if not n["name"]:
                        continue
                    nms.append(n["name"])
                if nms:
                    t = k[:-4]
                    cv[f"{t}_kwd"] = nms
                    cv[f"{t}_tks"] = rag_tokenizer.tokenize(" ".join(nms))
            except Exception:
                logging.exception("parse {} {}".format(str(traceback.format_exc()), cv[k]))
                cv[k] = []

        # tokenize fields
        if k in tks_fld:
            cv[f"{k}_tks"] = rag_tokenizer.tokenize(cv[k])
            if k in small_tks_fld:
                cv[f"{k}_sm_tks"] = rag_tokenizer.tokenize(cv[f"{k}_tks"])

        # keyword fields
        if k in kwd_fld:
            cv[f"{k}_kwd"] = [n.lower()
                                           for n in re.split(r"[\t,，；;. ]",
                                                             re.sub(r"([^a-zA-Z])[ ]+([^a-zA-Z ])", r"\1，\2", cv[k])
                                                             ) if n]

        if k in num_fld and cv.get(k):
            cv[f"{k}_int"] = cv[k]

    cv["email_kwd"] = cv.get("email_tks", "").replace(" ", "")
    # for name field
    if cv.get("name"):
        nm = re.sub(r"[\n——\-\(（\+].*", "", cv["name"].strip())
        nm = re.sub(r"[ \t　]+", " ", nm)
        if re.match(r"[a-zA-Z ]+$", nm):
            if len(nm.split()) > 1:
                cv["name"] = nm
            else:
                nm = ""
        elif nm and (surname.isit(nm[0]) or surname.isit(nm[:2])):
            nm = re.sub(r"[a-zA-Z]+.*", "", nm[:5])
        else:
            nm = ""
        cv["name"] = nm.strip()
        name = cv["name"]

        # name pingyin and its prefix
        cv["name_py_tks"] = " ".join(PY.get_pinyins(nm[:20], '')) + " " + " ".join(PY.get_pinyins(nm[:20], ' '))
        cv["name_py_pref0_tks"] = ""
        cv["name_py_pref_tks"] = ""
        for py in PY.get_pinyins(nm[:20], ''):
            for i in range(2, len(py) + 1):
                cv["name_py_pref_tks"] += " " + py[:i]
        for py in PY.get_pinyins(nm[:20], ' '):
            py = py.split()
            for i in range(1, len(py) + 1):
                cv["name_py_pref0_tks"] += " " + "".join(py[:i])

        cv["name_kwd"] = name
        cv["name_pinyin_kwd"] = PY.get_pinyins(nm[:20], ' ')[:3]
        cv["name_tks"] = (
                rag_tokenizer.tokenize(name) + " " + (" ".join(list(name)) if not re.match(r"[a-zA-Z ]+$", name) else "")
        ) if name else ""
    else:
        cv["integerity_flt"] /= 2.

    if cv.get("phone"):
        r = re.search(r"(1[3456789][0-9]{9})", cv["phone"])
        if not r:
            cv["phone"] = ""
        else:
            cv["phone"] = r.group(1)

    # deal with date  fields
    if cv.get("updated_at") and isinstance(cv["updated_at"], datetime.datetime):
        cv["updated_at_dt"] = cv["updated_at"].strftime('%Y-%m-%d %H:%M:%S')
    else:
        y, m, d = getYMD(str(cv.get("updated_at", "")))
        if not y:
            y = "2012"
        if not m:
            m = "01"
        if not d:
            d = "01"
        cv["updated_at_dt"] = "%s-%02d-%02d 00:00:00" % (y, int(m), int(d))
        # long text tokenize

    if cv.get("responsibilities"):
        cv["responsibilities_ltks"] = rag_tokenizer.tokenize(rmHtmlTag(cv["responsibilities"]))

    # for yes or no field
    fea = []
    for f, y, n in is_fld:
        if f not in cv:
            continue
        if cv[f] == '是':
            fea.append(y)
        if cv[f] == '否':
            fea.append(n)

    if fea:
        cv["tag_kwd"] = fea

    cv = forEdu(cv)
    cv = forProj(cv)
    cv = forWork(cv)
    cv = birth(cv)

    cv["corp_proj_sch_deg_kwd"] = [c for c in cv.get("corp_tag_kwd", [])]
    for i in range(len(cv["corp_proj_sch_deg_kwd"])):
        for j in cv.get("sch_rank_kwd", []):
            cv["corp_proj_sch_deg_kwd"][i] += "+" + j
    for i in range(len(cv["corp_proj_sch_deg_kwd"])):
        if cv.get("highest_degree_kwd"):
            cv["corp_proj_sch_deg_kwd"][i] += "+" + cv["highest_degree_kwd"]

    try:
        if not cv.get("work_exp_flt") and cv.get("work_start_time"):
            if re.match(r"[0-9]{9,}", str(cv["work_start_time"])):
                cv["work_start_dt"] = turnTm2Dt(cv["work_start_time"])
                cv["work_exp_flt"] = (time.time() - int(int(cv["work_start_time"]) / 1000)) / 3600. / 24. / 365.
            elif re.match(r"[0-9]{4}[^0-9]", str(cv["work_start_time"])):
                y, m, d = getYMD(str(cv["work_start_time"]))
                cv["work_start_dt"] = "%s-%02d-%02d 00:00:00" % (y, int(m), int(d))
                cv["work_exp_flt"] = int(str(datetime.date.today())[0:4]) - int(y)
    except Exception as e:
        logging.exception("parse {} ==> {}".format(e, cv.get("work_start_time")))
    if "work_exp_flt" not in cv and cv.get("work_experience", 0):
        cv["work_exp_flt"] = int(cv["work_experience"]) / 12.

    keys = list(cv.keys())
    for k in keys:
        if not re.search(r"_(fea|tks|nst|dt|int|flt|ltks|kwd|id)$", k):
            del cv[k]
    for k in cv.keys():
        if not re.search("_(kwd|id)$", k) or not isinstance(cv[k], list):
            continue
        cv[k] = list(set([re.sub("(市)$", "", str(n)) for n in cv[k] if n not in ['中国', '0']]))
    keys = [k for k in cv.keys() if re.search(r"_feas*$", k)]
    for k in keys:
        if cv[k] <= 0:
            del cv[k]

    cv["tob_resume_id"] = str(cv["tob_resume_id"])
    cv["id"] = cv["tob_resume_id"]
    logging.debug("CCCCCCCCCCCCCCC")

    return dealWithInt64(cv)