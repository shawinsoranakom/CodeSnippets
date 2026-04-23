def _build_chunk_document(filename: str, resume: dict,
                          lang: str = "Chinese") -> list[dict]:
    """
    Build a list of document chunks from structured resume information

    Each field generates an independent chunk containing tokenization results and metadata.
    Compatible with the build_chunks flow in task_executor.py.

    Key design: Each chunk redundantly includes key identity fields (name, phone, email, etc.),
    so that when any chunk is retrieved, the candidate's identity can be immediately identified.
    The full resume can be fetched via doc_id to get all chunks for complete information.

    Args:
        filename: File name
        resume: Structured resume information dictionary
        lang: Language parameter, default "Chinese"
    Returns:
        Document chunk list, each chunk contains content_with_weight, content_ltks,
        position_int, page_num_int, top_int and other fields
    """
    chunks = []
    # Get the corresponding field map version based on language parameter
    field_map = get_field_map(lang)
    doc = {
        "docnm_kwd": filename,
        "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", filename)),
    }
    doc["title_sm_tks"] = rag_tokenizer.fine_grained_tokenize(doc["title_tks"])

    # Extract key identity fields, redundantly written to each chunk
    # These fields are small in size but high in information density; once retrieved, the candidate can be immediately identified
    _IDENTITY_FIELDS = ("name_kwd", "phone_kwd", "email_tks", "gender_kwd",
                        "highest_degree_kwd", "work_exp_flt")
    identity_meta = {}
    for ik in _IDENTITY_FIELDS:
        iv = resume.get(ik)
        if not iv:
            continue
        if ik.endswith("_tks"):
            identity_meta[ik] = rag_tokenizer.tokenize(
                " ".join(iv) if isinstance(iv, list) else str(iv)
            )
        elif ik.endswith("_kwd"):
            identity_meta[ik] = iv if isinstance(iv, list) else str(iv)
        elif ik.endswith("_flt"):
            try:
                identity_meta[ik] = float(iv)
            except (ValueError, TypeError):
                pass
        else:
            identity_meta[ik] = str(iv)

    # Build resume summary text, appended to each chunk's content to improve semantic retrieval recall
    summary_parts = []
    _en = _is_english(lang)
    if resume.get("name_kwd"):
        summary_parts.append(f"{'Name' if _en else '姓名'}:{resume['name_kwd']}")
    if resume.get("phone_kwd"):
        summary_parts.append(f"{'Phone' if _en else '电话'}:{resume['phone_kwd']}")
    if resume.get("corporation_name_tks"):
        corp = resume["corporation_name_tks"]
        summary_parts.append(f"{'Company' if _en else '公司'}:{corp if isinstance(corp, str) else ' '.join(corp)}")
    if resume.get("highest_degree_kwd"):
        summary_parts.append(f"{'Degree' if _en else '学历'}:{resume['highest_degree_kwd']}")
    if resume.get("work_exp_flt"):
        if _en:
            summary_parts.append(f"Experience:{resume['work_exp_flt']}yrs")
        else:
            summary_parts.append(f"经验:{resume['work_exp_flt']}年")
    resume_summary = " | ".join(summary_parts) if summary_parts else ""

    # List fields that need per-element splitting (each experience/project generates a separate chunk to avoid oversized merged chunks)
    _SPLIT_LIST_FIELDS = {"work_desc_tks", "project_desc_tks"}

    # Basic info field set: these fields should be merged into one chunk to avoid splitting name, phone, email, etc.
    _BASIC_INFO_FIELDS = {
        "name_kwd", "name_pinyin_kwd", "gender_kwd", "age_int",
        "phone_kwd", "email_tks", "birth_dt", "work_exp_flt",
        "position_name_tks", "expect_city_names_tks",
        "expect_position_name_tks",
    }

    # Education field set: degree, school, major, tags, etc. should be merged into one chunk
    _EDUCATION_FIELDS = {
        "first_school_name_tks", "first_degree_kwd", "highest_degree_kwd",
        "first_major_tks", "edu_first_fea_kwd", "degree_kwd", "major_tks",
        "school_name_tks", "sch_rank_kwd", "edu_fea_kwd", "edu_end_int",
    }

    # Skills & certificates field set: skills, languages, certificates are small, merge into one chunk
    _SKILL_CERT_FIELDS = {
        "skill_tks", "language_tks", "certificate_tks",
    }

    # Work overview field set: company list, industry, most recent company merged into one chunk
    _WORK_OVERVIEW_FIELDS = {
        "corporation_name_tks", "corp_nm_tks", "industry_name_tks",
    }

    # All merge groups: (field_set, group_title) tuple list
    _MERGE_GROUPS = [
        (_BASIC_INFO_FIELDS, "Basic Info" if _en else "基本信息"),
        (_EDUCATION_FIELDS, "Education" if _en else "教育背景"),
        (_SKILL_CERT_FIELDS, "Skills & Certificates" if _en else "技能与证书"),
        (_WORK_OVERVIEW_FIELDS, "Work Overview" if _en else "工作概况"),
    ]

    # Collect all fields that need merge processing; skip them during individual iteration
    _ALL_MERGED_FIELDS = set()
    for fields_set, _ in _MERGE_GROUPS:
        _ALL_MERGED_FIELDS.update(fields_set)

    # Merge fields by group, generating one chunk per group
    for fields_set, group_title in _MERGE_GROUPS:
        group_parts = []
        group_field_values = {}  # Store structured values for each field, to be written into chunk
        for field_key in field_map:
            if field_key not in fields_set:
                continue
            value = resume.get(field_key)
            if not value:
                continue
            field_desc = field_map[field_key]
            if isinstance(value, list):
                text_value = " ".join(str(v) for v in value if v)
            else:
                text_value = str(value)
            if not text_value.strip():
                continue
            group_parts.append(f"{field_desc}: {text_value}")
            group_field_values[field_key] = value

        if not group_parts:
            continue

        content = f"{group_title}\n" + "\n".join(group_parts)
        if resume_summary:
            content += f"\n[{resume_summary}]"
        chunk = {
            "content_with_weight": content,
            "content_ltks": rag_tokenizer.tokenize(content),
            "content_sm_ltks": rag_tokenizer.fine_grained_tokenize(
                rag_tokenizer.tokenize(content)
            ),
        }
        chunk.update(doc)
        # Redundantly write identity fields
        for mk, mv in identity_meta.items():
            chunk[mk] = mv
        # Write each field's structured value into chunk (for structured retrieval)
        for fk, fv in group_field_values.items():
            if fk.endswith("_tks"):
                text_val = " ".join(str(v) for v in fv) if isinstance(fv, list) else str(fv)
                chunk[fk] = rag_tokenizer.tokenize(text_val)
            elif fk.endswith("_kwd"):
                chunk[fk] = fv if isinstance(fv, list) else str(fv)
            elif fk.endswith("_int"):
                try:
                    chunk[fk] = int(fv)
                except (ValueError, TypeError):
                    pass
            elif fk.endswith("_flt"):
                try:
                    chunk[fk] = float(fv)
                except (ValueError, TypeError):
                    pass
            else:
                chunk[fk] = str(fv)
        chunks.append(chunk)

    # Iterate over field map, generating a chunk for each non-merged field with a value
    for field_key, field_desc in field_map.items():
        # Skip fields already processed in merge groups
        if field_key in _ALL_MERGED_FIELDS:
            continue
        value = resume.get(field_key)
        if not value:
            continue

        # For work/project descriptions (long text lists), split into multiple chunks per element
        if field_key in _SPLIT_LIST_FIELDS and isinstance(value, list):
            # Get company name list to add context to each work description
            corp_list = resume.get("corp_nm_tks", []) if field_key == "work_desc_tks" else []
            project_list = resume.get("project_tks", []) if field_key == "project_desc_tks" else []
            # Get detailed info for each work experience entry (time period, years)
            work_details = resume.get("_work_exp_details", []) if field_key == "work_desc_tks" else []

            for idx, item in enumerate(value):
                item_text = str(item).strip()
                if not item_text:
                    continue

                # Add company/project name prefix to each description for context
                if field_key == "work_desc_tks" and idx < len(work_details):
                    # Use detailed info to build prefix, including company, time range, years
                    detail = work_details[idx]
                    company = detail.get("company", "")
                    start_d = detail.get("start_date", "")
                    end_d = detail.get("end_date", "")
                    years = detail.get("years", 0)
                    # Build time range text
                    time_parts = []
                    if start_d:
                        time_range = f"{start_d}-{end_d}" if end_d else str(start_d)
                        time_parts.append(time_range)
                    if years > 0:
                        time_parts.append(f"{years}{'yrs' if _en else '年'}")
                    time_text = " ".join(time_parts)
                    if company and time_text:
                        content_prefix = f"{field_desc}（{company} {time_text}）"
                    elif company:
                        content_prefix = f"{field_desc}（{company}）"
                    else:
                        content_prefix = f"{field_desc}（{'#' if _en else '第'}{idx + 1}{'' if _en else '段'}）"
                elif field_key == "work_desc_tks" and idx < len(corp_list):
                    content_prefix = f"{field_desc}（{corp_list[idx]}）"
                elif field_key == "project_desc_tks" and idx < len(project_list):
                    content_prefix = f"{field_desc}（{project_list[idx]}）"
                else:
                    content_prefix = f"{field_desc}（{'#' if _en else '第'}{idx + 1}{'' if _en else '段'}）"

                if resume_summary:
                    content = f"{content_prefix}: {item_text}\n[{resume_summary}]"
                else:
                    content = f"{content_prefix}: {item_text}"

                chunk = {
                    "content_with_weight": content,
                    "content_ltks": rag_tokenizer.tokenize(content),
                    "content_sm_ltks": rag_tokenizer.fine_grained_tokenize(
                        rag_tokenizer.tokenize(content)
                    ),
                }
                chunk.update(doc)

                # Redundantly write identity fields
                for mk, mv in identity_meta.items():
                    if mk != field_key:
                        chunk[mk] = mv

                # Tokenization result for current segment
                chunk[field_key] = rag_tokenizer.tokenize(item_text)
                chunks.append(chunk)
            continue

        # Merge list values into text
        if isinstance(value, list):
            text_value = " ".join(str(v) for v in value if v)
        else:
            text_value = str(value)

        if not text_value.strip():
            continue

        # Build chunk content: "field_desc: field_value", append summary for semantic association
        if resume_summary and field_key not in ("name_kwd", "phone_kwd"):
            content = f"{field_desc}: {text_value}\n[{resume_summary}]"
        else:
            content = f"{field_desc}: {text_value}"

        chunk = {
            "content_with_weight": content,
            "content_ltks": rag_tokenizer.tokenize(content),
            "content_sm_ltks": rag_tokenizer.fine_grained_tokenize(
                rag_tokenizer.tokenize(content)
            ),
        }
        chunk.update(doc)

        # Redundantly write identity fields (do not overwrite the current field's own value)
        for mk, mv in identity_meta.items():
            if mk != field_key:
                chunk[mk] = mv

        # Write resume field value into the chunk's corresponding field (for structured retrieval)
        if field_key.endswith("_tks"):
            chunk[field_key] = rag_tokenizer.tokenize(text_value)
        elif field_key.endswith("_kwd"):
            if isinstance(value, list):
                chunk[field_key] = value
            else:
                chunk[field_key] = text_value
        elif field_key.endswith("_int"):
            try:
                chunk[field_key] = int(value)
            except (ValueError, TypeError):
                pass
        elif field_key.endswith("_flt"):
            try:
                chunk[field_key] = float(value)
            except (ValueError, TypeError):
                pass
        else:
            chunk[field_key] = text_value

        chunks.append(chunk)

    # If no chunks were generated, create at least one chunk containing the name
    if not chunks:
        name = resume.get("name_kwd", "Unknown" if _en else "未知")
        content = f"{'Name' if _en else '姓名'}: {name}"
        chunk = {
            "content_with_weight": content,
            "content_ltks": rag_tokenizer.tokenize(content),
            "content_sm_ltks": rag_tokenizer.fine_grained_tokenize(
                rag_tokenizer.tokenize(content)
            ),
        }
        chunk.update(doc)
        chunks.append(chunk)

    # Write coordinate info to each chunk (position_int, page_num_int, top_int)
    #
    # Resume chunks are split by semantic fields (basic info, education, work description, etc.),
    # not by PDF physical regions. Field values may be scattered across multiple locations in the PDF,
    # and using text matching to reverse-lookup coordinates would cause disordered sorting.
    #
    # Therefore, assign incrementing coordinates based on chunk generation order (i.e., semantic logical order),
    # ensuring display order: basic info -> education -> skills/certs -> work overview -> work desc -> project desc...
    #
    # add_positions input format: [(page, left, right, top, bottom), ...]
    #   - page starts from 0, function internally stores +1
    #   - task_executor sorts by page_num_int and top_int (page first, then Y coordinate)
    from rag.nlp import add_positions

    for i, ck in enumerate(chunks):
        # All chunks placed on page=0, top increments by index to ensure logical ordering
        add_positions(ck, [[0, 0, 0, i, i]])

    return chunks