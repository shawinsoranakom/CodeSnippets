def parse_with_llm(indexed_text: str, lines: list[str], tenant_id , lang: str) -> Optional[dict]:
    """
    Extract resume info using parallel task decomposition strategy (ref SmartResume Section 3.2).

    Decomposes extraction into four independent subtasks executed in parallel:
    1. Basic info (name, phone, skills, self-evaluation, etc.)
    2. Work experience (company, position, description line ranges)
    3. Education background (school, major, degree)
    4. Project experience (project name, role, description line ranges)

    Args:
        indexed_text: Line-indexed resume text
        lines: List of original line texts (for index-based extraction)
        lang: Language
    Returns:
        Merged structured resume dictionary, or None on failure
    """
    try:
        # Execute four subtasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_basic = executor.submit(_extract_basic_info, indexed_text, tenant_id , lang)
            future_work = executor.submit(_extract_work_experience, indexed_text, tenant_id , lang)
            future_edu = executor.submit(_extract_education, indexed_text, tenant_id, lang)
            future_project = executor.submit(_extract_project_experience, indexed_text, tenant_id , lang)

            basic_info = future_basic.result(timeout=60)
            work_exp = future_work.result(timeout=60)
            education = future_edu.result(timeout=60)
            project_exp = future_project.result(timeout=60)

        # Merge results
        resume = {}

        # Merge basic info
        if basic_info:
            resume.update(basic_info)
            logger.info(f"Basic info extraction succeeded: {len(basic_info)} fields")

        # Process work experience (index pointer extraction)
        if work_exp and "workExperience" in work_exp:
            experiences = work_exp["workExperience"]
            companies = []
            positions = []
            work_descs = []
            # Save detailed info for each experience (dates, years) for chunk generation
            work_exp_details = []
            for exp in experiences:
                company = exp.get("company", "")
                position = exp.get("position", "")
                start_date = exp.get("start_date", "")
                end_date = exp.get("end_date", "")
                # Calculate years for this experience entry
                years = _calc_single_exp_years(start_date, end_date)
                if company:
                    companies.append(company)
                if position:
                    positions.append(position)
                # Save detailed info for each experience entry
                work_exp_details.append({
                    "company": company,
                    "position": position,
                    "start_date": start_date,
                    "end_date": end_date,
                    "years": years,
                })
                # Index pointer mechanism: extract description from original text by line range
                # Use _extract_description_from_range to filter header lines (ref SmartResume)
                desc_lines = exp.get("desc_lines", [])
                if isinstance(desc_lines, list) and len(desc_lines) == 2:
                    desc = _extract_description_from_range(
                        desc_lines, lines, company=company, position=position
                    )
                    if desc.strip():
                        work_descs.append(desc.strip())

            if companies:
                resume["corp_nm_tks"] = companies
                resume["corporation_name_tks"] = companies[0]
            if positions:
                resume["position_name_tks"] = positions
            if work_descs:
                resume["work_desc_tks"] = work_descs
            # Save experience details for _build_chunk_document
            if work_exp_details:
                resume["_work_exp_details"] = work_exp_details
            # Calculate total work years from each experience's dates (overrides LLM's guess in basic info)
            calculated_years = _calculate_work_years(experiences)
            if calculated_years > 0:
                resume["work_exp_flt"] = calculated_years
            logger.info(f"Work experience extraction succeeded: {len(experiences)} entries, calculated total years: {calculated_years}")

        # Process education background
        if education and "education" in education:
            edu_list = education["education"]
            schools = []
            majors = []
            degrees = []
            for edu in edu_list:
                if edu.get("school"):
                    schools.append(edu["school"])
                if edu.get("major"):
                    majors.append(edu["major"])
                if edu.get("degree"):
                    degrees.append(edu["degree"])
                # Extract graduation year
                end_date = edu.get("end_date", "")
                if end_date and not resume.get("edu_end_int"):
                    year_match = re.search(r"(19|20)\d{2}", str(end_date))
                    if year_match:
                        resume["edu_end_int"] = int(year_match.group(0))

            if schools:
                resume["school_name_tks"] = schools
                resume["first_school_name_tks"] = schools[-1]  # Earliest school is usually last
            if majors:
                resume["major_tks"] = majors
                resume["first_major_tks"] = majors[-1]
            if degrees:
                resume["degree_kwd"] = degrees
                # Infer highest degree (supports both Chinese and English degree names)
                degree_rank = {
                    "博士": 5, "PhD": 5, "Doctor": 5,
                    "硕士": 4, "Master": 4, "MBA": 4, "EMBA": 4, "MPA": 4,
                    "本科": 3, "Bachelor": 3,
                    "大专": 2, "专科": 2, "Associate": 2, "Diploma": 2,
                    "高中": 1, "High School": 1,
                }
                highest = max(degrees, key=lambda d: degree_rank.get(d, 0), default="")
                if highest:
                    resume["highest_degree_kwd"] = highest
                resume["first_degree_kwd"] = degrees[-1] if degrees else ""
            logger.info(f"Education extraction succeeded: {len(edu_list)} entries")

        # Process project experience (index pointer extraction, similar to work experience)
        if project_exp and "projectExperience" in project_exp:
            projects = project_exp["projectExperience"]
            project_names = []
            project_descs = []
            for proj in projects:
                name = proj.get("project_name", "")
                if name:
                    project_names.append(name)
                # Index pointer mechanism: extract project description from original text by line range
                desc_lines = proj.get("desc_lines", [])
                if isinstance(desc_lines, list) and len(desc_lines) == 2:
                    desc = _extract_description_from_range(
                        desc_lines, lines, company=name, position=proj.get("role", "")
                    )
                    if desc.strip():
                        project_descs.append(desc.strip())

            if project_names:
                resume["project_tks"] = project_names
            if project_descs:
                resume["project_desc_tks"] = project_descs
            logger.info(f"Project experience extraction succeeded: {len(projects)} entries")

        if not resume.get("name_kwd"):
            resume["name_kwd"] = "Unknown" if _is_english(lang) else "未知"

        return resume if len(resume) > 2 else None

    except concurrent.futures.TimeoutError:
        logger.warning("LLM parallel extraction timed out")
        return None
    except Exception as e:
        logger.warning(f"LLM parallel extraction failed: {e}")
        return None