def parse_with_regex(text: str, lang: str = "Chinese") -> dict:
    """
    Parse resume text using regex (fallback strategy)

    When LLM parsing fails, use regex to extract basic structured info from text.

    Args:
        text: Resume text content (without line number index)
        lang: Language parameter, default "Chinese"
    Returns:
        Structured resume info dictionary
    """
    resume: dict = {}
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # --- Extract Name ---
    if _is_english(lang):
        # English resume: extract from "Name: XXX" format
        for line in lines[:30]:
            name_match = re.search(r'(?:Name|Full\s*Name)\s*[:：]\s*([A-Za-z][A-Za-z\s\-\.]{1,40})', line, re.IGNORECASE)
            if name_match:
                resume["name_kwd"] = name_match.group(1).strip()
                break
        # English resume strategy 2: first line if short text without digits, may be a name
        if "name_kwd" not in resume and lines:
            first = lines[0].strip()
            if len(first) <= 40 and not re.search(r"\d", first) and re.match(r'^[A-Za-z][A-Za-z\s\-\.]+$', first):
                resume["name_kwd"] = first
    else:
        # Chinese resume: extract from "姓名：XXX" format
        for line in lines[:30]:
            name_match = re.search(r'姓\s*名\s*[:：]\s*([\u4e00-\u9fa5]{2,4})', line)
            if name_match:
                resume["name_kwd"] = name_match.group(1)
                break

        # Strategy 2: search first 20 lines for standalone Chinese names (2-4 chars), excluding common title words
        if "name_kwd" not in resume:
            title_words = {
                "个人", "简历", "求职", "应聘", "基本", "信息", "概述", "简介",
                "教育", "工作", "经历", "经验", "技能", "项目", "自我", "评价",
                "专业", "技术", "证书", "语言", "能力", "培训", "荣誉", "奖项",
            }
            for line in lines[:20]:
                if any(w in line for w in title_words):
                    continue
                if re.search(r'[:：]', line) and len(line) > 6:
                    continue
                cleaned = re.sub(r"^[A-Za-z_\-\d\s]+\s+", "", line)
                cleaned = re.sub(r"\s+[A-Za-z_\-\d\s]+$", "", cleaned).strip()
                if 2 <= len(cleaned) <= 4 and re.match(r"^[\u4e00-\u9fa5]{2,4}$", cleaned):
                    resume["name_kwd"] = cleaned
                    break

        # Strategy 3: first line if short without digits, may be a name
        if "name_kwd" not in resume and lines:
            first = lines[0].strip()
            if len(first) <= 10 and not re.search(r"\d", first):
                cn_part = re.findall(r'[\u4e00-\u9fa5]+', first)
                if cn_part and 2 <= len(cn_part[0]) <= 4:
                    resume["name_kwd"] = cn_part[0]

    # --- Extract Phone Number ---
    phones = re.findall(r"1[3-9]\d{9}", text)
    if phones:
        resume["phone_kwd"] = phones[0]

    # --- Extract Email ---
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if emails:
        resume["email_tks"] = emails[0]

    # --- Extract Gender ---
    if _is_english(lang):
        # English resume: extract from "Gender: Male/Female" format
        gender_label = re.search(r'(?:Gender|Sex)\s*[:：]\s*(Male|Female|M|F)', text, re.IGNORECASE)
        if gender_label:
            raw = gender_label.group(1).strip().upper()
            resume["gender_kwd"] = "Male" if raw in ("M", "MALE") else "Female"
        else:
            gender_match = re.search(r'\b(Male|Female)\b', text[:500], re.IGNORECASE)
            if gender_match:
                resume["gender_kwd"] = gender_match.group(1).capitalize()
    else:
        # Chinese resume: extract from "性别：男/女" format
        gender_label = re.search(r'性\s*别\s*[:：]\s*(男|女)', text)
        if gender_label:
            resume["gender_kwd"] = gender_label.group(1)
        else:
            gender_match = re.search(r"(男|女)", text[:500])
            if gender_match:
                resume["gender_kwd"] = gender_match.group(1)

    # --- Extract Age ---
    if _is_english(lang):
        # English resume: match "25 years old" or "Age: 25"
        age_match = re.search(r'(?:Age)\s*[:：]\s*(\d{1,2})', text, re.IGNORECASE)
        if not age_match:
            age_match = re.search(r'(\d{1,2})\s*years?\s*old', text, re.IGNORECASE)
        if age_match:
            resume["age_int"] = int(age_match.group(1))
    else:
        # Chinese resume: match "25岁"
        age_match = re.search(r"(\d{1,2})\s*岁", text)
        if age_match:
            resume["age_int"] = int(age_match.group(1))

    # --- Extract Date of Birth ---
    if _is_english(lang):
        # English resume: match "1990-01-15" or "Jan 15, 1990" etc.
        birth_match = re.search(r'(?:Birth|DOB|Date\s*of\s*Birth)\s*[:：]\s*(.{6,20})', text, re.IGNORECASE)
        if birth_match:
            resume["birth_dt"] = birth_match.group(1).strip()
        else:
            birth_match = re.search(r"(19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}", text)
            if birth_match:
                resume["birth_dt"] = birth_match.group(0)
    else:
        # Chinese resume: match "1990年1月15日" or "1990-01-15"
        birth_match = re.search(r"(19|20)\d{2}[年/-]\d{1,2}[月/-]\d{1,2}", text)
        if birth_match:
            resume["birth_dt"] = birth_match.group(0)

    # --- Extract Education Level ---
    degree_keywords_zh = ["博士", "硕士", "本科", "大专", "专科", "高中", "MBA", "EMBA", "MPA"]
    degree_keywords_en = ["PhD", "Master", "Bachelor", "Associate", "Diploma", "High School",
                          "MBA", "EMBA", "MPA", "Doctor"]
    degree_keywords = degree_keywords_en if _is_english(lang) else degree_keywords_zh
    found_degrees = [d for d in degree_keywords if d in text]
    if found_degrees:
        resume["degree_kwd"] = found_degrees

    # --- Extract School ---
    if _is_english(lang):
        # English resume: match "University/College/Institute/School" keywords
        schools = re.findall(
            r'([A-Z][A-Za-z\s\-&]{2,40}(?:University|College|Institute|School|Academy))',
            text
        )
        # Remove extra whitespace
        schools = [re.sub(r'\s+', ' ', s).strip() for s in schools]
    else:
        # Chinese resume: match "XX大学/学院/职业技术学院"
        schools = re.findall(r"[\u4e00-\u9fa5]{2,15}(?:大学|学院|职业技术学院)", text)
    if schools:
        resume["school_name_tks"] = list(set(schools))
        resume["first_school_name_tks"] = schools[0]

    # --- Extract Major ---
    if _is_english(lang):
        # English resume: match "Major: XXX" / "Field of Study: XXX" / "Specialization: XXX"
        majors = re.findall(
            r'(?:Major|Field\s*of\s*Study|Specialization|Concentration)\s*[:：]\s*([A-Za-z\s\-&,]{2,40})',
            text, re.IGNORECASE
        )
        majors = [m.strip() for m in majors if m.strip()]
    else:
        # Chinese resume: match "专业：XXX"
        majors = re.findall(r"专业[:：]\s*([\u4e00-\u9fa5]{2,20})", text)
    if majors:
        resume["major_tks"] = majors
        resume["first_major_tks"] = majors[0]

    # --- Extract Company Names ---
    if _is_english(lang):
        # English resume: match common company suffixes
        en_company_patterns = [
            r'([A-Z][A-Za-z\s\-&,\.]{2,40}(?:Inc\.|Corp\.|Ltd\.|LLC|Co\.|Company|Group|Technologies|Technology|Solutions|Consulting|Services|Bank))',
        ]
        companies = []
        for pattern in en_company_patterns:
            companies.extend(re.findall(pattern, text))
        companies = [re.sub(r'\s+', ' ', c).strip() for c in companies]
    else:
        # Chinese resume: match "XX有限公司" format
        company_patterns = [
            r"[\u4e00-\u9fa5]{2,20}[（(][\u4e00-\u9fa5]{2,10}[)）](?:科技|信息技术|网络科技)?(?:股份)?有限公司",
            r"[\u4e00-\u9fa5]{4,20}(?:科技|信息技术|网络科技|银行)?(?:股份)?有限公司",
        ]
        companies = []
        for pattern in company_patterns:
            companies.extend(re.findall(pattern, text))

    unique_companies = []
    seen = set()
    # Filter verb list (bilingual)
    filter_verbs = (
        ["completed", "conducted", "implemented", "responsible", "participated", "developed"]
        if _is_english(lang)
        else ["完成", "进行", "实施", "负责", "参与", "开发"]
    )
    min_len = 3 if _is_english(lang) else 6
    for c in companies:
        if len(c) < min_len or any(v in c.lower() for v in filter_verbs) or c in seen:
            continue
        is_sub = False
        for existing in list(unique_companies):
            if c in existing:
                is_sub = True
                break
            if existing in c:
                unique_companies.remove(existing)
                seen.discard(existing)
        if not is_sub:
            unique_companies.append(c)
            seen.add(c)

    if unique_companies:
        resume["corp_nm_tks"] = unique_companies
        resume["corporation_name_tks"] = unique_companies[0]

    # --- Extract Position (improved: context constraints to reduce noise) ---
    if _is_english(lang):
        # English resume: Strategy 1 - extract from "Title: XXX" / "Position: XXX" / "Role: XXX" format
        position_label_matches = re.findall(
            r'(?:Title|Position|Role|Job\s*Title)\s*[:：]\s*([A-Za-z\s\-/&]{2,30})',
            text, re.IGNORECASE
        )
        positions = [p.strip() for p in position_label_matches if p.strip()]

        # English resume: Strategy 2 - match common position suffix keywords
        en_position_suffixes = [
            "Engineer", "Manager", "Director", "Supervisor", "Specialist",
            "Designer", "Consultant", "Assistant", "Architect", "Analyst",
            "Developer", "Lead", "Officer", "Coordinator", "Administrator",
            "Intern", "VP", "President",
        ]
        for line in lines:
            if len(line) > 60:
                continue  # Skip overly long lines (usually description text)
            for suffix in en_position_suffixes:
                match = re.search(rf'([A-Za-z\s\-]{{1,25}}{suffix})\b', line, re.IGNORECASE)
                if match:
                    pos = match.group(1).strip()
                    # Filter out matches that are clearly not positions (contain verbs)
                    filter_pos_verbs = ["responsible", "participated", "completed", "developed", "designed"]
                    if not any(v in pos.lower() for v in filter_pos_verbs) and len(pos) > 3:
                        positions.append(pos)
    else:
        # Chinese resume: Strategy 1 - extract from "职位/岗位：XXX" format
        position_label_matches = re.findall(
            r'(?:职位|岗位|职务|职称|担任)\s*[:：]\s*([\u4e00-\u9fa5a-zA-Z]{2,15})',
            text
        )
        positions = list(position_label_matches)

        # Chinese resume: Strategy 2 - extract from work experience paragraphs (company name followed by position)
        for line in lines:
            pos_match = re.search(
                r'(?:有限公司|集团|银行)\s+([\u4e00-\u9fa5]{2,8}(?:工程师|经理|总监|主管|专员|设计师|顾问|助理|架构师|分析师|运营|产品))',
                line
            )
            if pos_match:
                positions.append(pos_match.group(1))

        # Chinese resume: Strategy 3 - position keywords in standalone lines (length-limited to avoid matching description text)
        position_suffixes = ["工程师", "经理", "总监", "主管", "专员", "设计师", "顾问",
                             "助理", "架构师", "分析师", "开发者", "负责人"]
        for line in lines:
            if len(line) > 20:
                continue  # Skip overly long lines
            for suffix in position_suffixes:
                match = re.search(rf'([\u4e00-\u9fa5]{{1,6}}{suffix})', line)
                if match:
                    pos = match.group(1)
                    if not any(v in pos for v in ["负责", "参与", "完成", "开发了", "设计了"]):
                        positions.append(pos)

    if positions:
        # Deduplicate while preserving order
        seen_pos = set()
        unique_positions = []
        for p in positions:
            if p not in seen_pos:
                seen_pos.add(p)
                unique_positions.append(p)
        resume["position_name_tks"] = unique_positions

    # --- Extract Years of Experience ---
    if _is_english(lang):
        # English resume: match "5 years experience" / "5+ years of experience"
        work_exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|work)', text, re.IGNORECASE)
        if work_exp_match:
            resume["work_exp_flt"] = float(work_exp_match.group(1))
    else:
        # Chinese resume: match "5年...经验"
        work_exp_match = re.search(r"(\d+)\s*年.*?经验", text)
        if work_exp_match:
            resume["work_exp_flt"] = float(work_exp_match.group(1))

    # --- Extract Graduation Year ---
    if _is_english(lang):
        # English resume: match "Graduated 2020" / "Graduation: 2020" / "Class of 2020"
        grad_match = re.search(r'(?:Graduat(?:ed|ion)|Class\s*of)\s*[:：]?\s*((?:19|20)\d{2})', text, re.IGNORECASE)
        if grad_match:
            resume["edu_end_int"] = int(grad_match.group(1))
    else:
        # Chinese resume: match "2020年...毕业"
        grad_match = re.search(r"((?:19|20)\d{2})\s*年.*?毕业", text)
        if grad_match:
            resume["edu_end_int"] = int(grad_match.group(1))

    if "name_kwd" not in resume:
        resume["name_kwd"] = "Unknown" if _is_english(lang) else "未知"

    return resume