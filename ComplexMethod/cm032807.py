def _postprocess_resume(resume: dict, lines: list[str], lang: str = "Chinese") -> dict:
    """
    Four-phase post-processing pipeline (ref: SmartResume Section 3.2.3)

    1. Source text validation: check if key fields can be found in the original text
    2. Domain normalization: standardize date formats, clean company name suffix noise
    3. Contextual deduplication: remove duplicate company/school entries
    4. Field completion: ensure all required fields exist

    Args:
        resume: Raw resume dictionary extracted by LLM
        lines: Original line text list (for source text validation)
        lang: Language parameter, default "Chinese"
    Returns:
        Post-processed resume dictionary
    """
    _en = _is_english(lang)
    full_text = "\n".join(lines) if lines else ""
    # Normalize full text for comparison (ref: SmartResume _validate_fields_in_text)
    norm_full_text = _normalize_for_comparison(full_text)

    # --- Phase 1: Source text validation (prune hallucinations, ref: SmartResume _validate_fields_in_text) ---
    # Name validation: clear if not found in source text (SmartResume strategy: discard hallucinated fields)
    _unknown_names = ("未知", "Unknown")
    if resume.get("name_kwd") and resume["name_kwd"] not in _unknown_names:
        norm_name = _normalize_for_comparison(resume["name_kwd"])
        if norm_full_text and norm_name and norm_name not in norm_full_text:
            logger.warning(f"Name '{resume['name_kwd']}' not found in source text, classified as LLM hallucination, cleared")
            resume["name_kwd"] = ""

    # Validate company names (strict matching: full name must appear in source text, no longer using loose 4-char prefix matching)
    if resume.get("corp_nm_tks") and norm_full_text:
        verified_companies = []
        for company in resume["corp_nm_tks"]:
            norm_company = _normalize_for_comparison(company)
            if norm_company and norm_company in norm_full_text:
                verified_companies.append(company)
            else:
                logger.debug(f"Company '{company}' not found in source text, filtered out")
        # Update even if all filtered out (SmartResume strategy: prefer missing over wrong)
        resume["corp_nm_tks"] = verified_companies
        if verified_companies:
            resume["corporation_name_tks"] = verified_companies[0]
        else:
            resume["corporation_name_tks"] = ""

    # Validate school names (ref: SmartResume _validate_fields_in_text)
    if resume.get("school_name_tks") and norm_full_text:
        verified_schools = []
        for school in resume["school_name_tks"]:
            norm_school = _normalize_for_comparison(school)
            if norm_school and norm_school in norm_full_text:
                verified_schools.append(school)
            else:
                logger.debug(f"School '{school}' not found in source text, filtered out")
        resume["school_name_tks"] = verified_schools
        if verified_schools:
            if resume.get("first_school_name_tks"):
                # Ensure first_school is also in the verified list
                if resume["first_school_name_tks"] not in verified_schools:
                    resume["first_school_name_tks"] = verified_schools[-1]
        else:
            resume["first_school_name_tks"] = ""

    # Validate position names
    if resume.get("position_name_tks") and norm_full_text:
        verified_positions = []
        for pos in resume["position_name_tks"]:
            norm_pos = _normalize_for_comparison(pos)
            if norm_pos and norm_pos in norm_full_text:
                verified_positions.append(pos)
        if verified_positions:
            resume["position_name_tks"] = verified_positions

    # --- Phase 2: Domain normalization ---
    # Standardize date format
    if resume.get("birth_dt"):
        resume["birth_dt"] = re.sub(r"[年月]", "-", str(resume["birth_dt"])).rstrip("-")

    # Clean non-digit characters from phone number (keep + sign)
    if resume.get("phone_kwd"):
        phone = re.sub(r"[^\d+]", "", str(resume["phone_kwd"]))
        if phone:
            resume["phone_kwd"] = phone

    # Standardize gender (output format determined by language parameter)
    if resume.get("gender_kwd"):
        gender = str(resume["gender_kwd"]).strip()
        if gender in ("male", "Male", "M", "m", "男"):
            resume["gender_kwd"] = "Male" if _en else "男"
        elif gender in ("female", "Female", "F", "f", "女"):
            resume["gender_kwd"] = "Female" if _en else "女"

    # --- Phase 3: Contextual deduplication ---
    for list_field in ["corp_nm_tks", "school_name_tks", "major_tks",
                       "position_name_tks", "skill_tks"]:
        if isinstance(resume.get(list_field), list):
            # Order-preserving deduplication
            seen = set()
            deduped = []
            for item in resume[list_field]:
                item_str = str(item).strip()
                if item_str and item_str not in seen:
                    seen.add(item_str)
                    deduped.append(item_str)
            resume[list_field] = deduped
    # --- Phase 3.4: work_desc_tks dedup by company name + time period ---
    # LLM often extracts the same company's content twice: once from the "Work Experience"
    # section and once from the "Project Experience" section, producing entries like
    # These have different descriptions (daily work vs project details), so content-based
    # Jaccard dedup cannot catch them. Instead, we detect duplicate companies by checking
    # if one company name is a substring of another AND their time periods overlap.
    # This also fixes the inflated work_exp_flt (e.g. 25.5 years instead of ~14).
    work_descs = resume.get("work_desc_tks", [])
    if len(work_descs) > 1:
        corp_names = resume.get("corp_nm_tks", [])
        work_details = resume.get("_work_exp_details", [])
        positions = resume.get("position_name_tks", [])
        kept_indices = []
        for i in range(len(work_descs)):
            is_dup = False
            corp_i = _normalize_for_comparison(corp_names[i]) if i < len(corp_names) else ""
            detail_i = work_details[i] if i < len(work_details) else {}
            start_i = detail_i.get("start_date", "")
            end_i = detail_i.get("end_date", "")
            # Parse dates for entry i once (reused across inner loop)
            dt_start_i = _parse_date_str(start_i) if start_i else None
            dt_end_i = _parse_date_str(end_i) if end_i else None
            for j in kept_indices:
                # Strategy A: company name substring + time period overlap
                corp_j = _normalize_for_comparison(corp_names[j]) if j < len(corp_names) else ""
                if corp_i and corp_j:
                    shorter_c, longer_c = (corp_i, corp_j) if len(corp_i) <= len(corp_j) else (corp_j, corp_i)
                    if shorter_c in longer_c:
                        # Check time period overlap using parsed dates
                        # Two intervals [s1,e1] and [s2,e2] overlap iff s1 <= e2 and s2 <= e1
                        # Use <= because resume dates are month-granularity (e.g. "2018.03" means "sometime in March 2018")
                        detail_j = work_details[j] if j < len(work_details) else {}
                        start_j = detail_j.get("start_date", "")
                        end_j = detail_j.get("end_date", "")
                        dt_start_j = _parse_date_str(start_j) if start_j else None
                        dt_end_j = _parse_date_str(end_j) if end_j else None
                        # Need at least one valid date on each side to compare
                        if dt_start_i and dt_start_j:
                            # Use far-future as default end if missing
                            eff_end_i = dt_end_i or datetime.datetime(2099, 12, 1)
                            eff_end_j = dt_end_j or datetime.datetime(2099, 12, 1)
                            if dt_start_i <= eff_end_j and dt_start_j <= eff_end_i:
                                is_dup = True
                                break
                        elif (start_i and start_j and start_i == start_j) or \
                                (end_i and end_j and end_i == end_j):
                            # Fallback: exact string match if date parsing fails
                            is_dup = True
                            break
                # Strategy B: content-based Jaccard similarity (fallback)
                norm_i = _normalize_for_comparison(work_descs[i])
                norm_j = _normalize_for_comparison(work_descs[j])
                shorter, longer = (norm_i, norm_j) if len(norm_i) <= len(norm_j) else (norm_j, norm_i)
                if shorter and longer and shorter in longer:
                    is_dup = True
                    break
                jac = _shingling_jaccard(work_descs[i], work_descs[j], n=5)
                if jac > 0.5:
                    is_dup = True
                    break
            if is_dup:
                dup_corp = corp_names[i] if i < len(corp_names) else f"#{i+1}"
                logger.debug(f"Work desc internal duplicate removed: {dup_corp}")
            else:
                kept_indices.append(i)
        # Only update when entries were actually removed
        if len(kept_indices) < len(work_descs):
            resume["work_desc_tks"] = [work_descs[i] for i in kept_indices]
            if corp_names:
                resume["corp_nm_tks"] = [corp_names[i] for i in kept_indices if i < len(corp_names)]
            if work_details:
                resume["_work_exp_details"] = [work_details[i] for i in kept_indices if i < len(work_details)]
            if positions:
                resume["position_name_tks"] = [positions[i] for i in kept_indices if i < len(positions)]
            # Recalculate work years based on deduplicated entries
            new_details = resume.get("_work_exp_details", [])
            if new_details:
                recalc_years = sum(d.get("years", 0) for d in new_details)
                recalc_years = round(recalc_years, 1)
                if recalc_years > 0:
                    resume["work_exp_flt"] = recalc_years
                    logger.info(f"Work years recalculated: {recalc_years} yrs (before dedup: {_calculate_work_years([{'start_date': d.get('start_date',''), 'end_date': d.get('end_date','')} for d in work_details])} yrs)")
            new_corps = resume.get("corp_nm_tks", [])
            if new_corps:
                resume["corporation_name_tks"] = new_corps[0]

    # --- Phase 3.5: Merge project_desc_tks into work_desc_tks ---
    # Instead of complex cross-dedup, we simply merge unique project descriptions into
    # work_desc_tks and clear project_desc_tks. This avoids the problem where LLM extracts
    # the same content into both fields with slightly different wording.
    # After merge, project_desc_tks is emptied so _build_chunk_document won't generate
    # duplicate chunks. Project names are preserved in project_tks for reference.
    work_descs = resume.get("work_desc_tks", [])
    project_descs = resume.get("project_desc_tks", [])
    # Save pre-merge project descriptions for debugging
    resume["_raw_project_descs"] = list(project_descs) if project_descs else []
    if project_descs:
        project_names = resume.get("project_tks", [])
        merged_count = 0
        skipped_count = 0
        for i, proj_desc in enumerate(project_descs):
            norm_proj = _normalize_for_comparison(proj_desc)
            if not norm_proj:
                continue
            # Check if this project desc already exists in work_descs (exact or near-duplicate)
            already_exists = False
            for wd in work_descs:
                norm_wd = _normalize_for_comparison(wd)
                if not norm_wd:
                    continue
                # Substring containment check
                shorter, longer = (norm_proj, norm_wd) if len(norm_proj) <= len(norm_wd) else (norm_wd, norm_proj)
                if shorter in longer:
                    already_exists = True
                    break
                # Jaccard similarity check
                if _shingling_jaccard(proj_desc, wd, n=5) > 0.5:
                    already_exists = True
                    break
            if already_exists:
                skipped_count += 1
                proj_name = project_names[i] if i < len(project_names) else f"#{i+1}"
                logger.debug(f"Project desc already in work_desc, skipped: {proj_name}")
            else:
                # Append to work_desc_tks with project name prefix for context
                proj_name = project_names[i] if i < len(project_names) else ""
                if proj_name:
                    proj_desc_with_prefix = f"[{proj_name}] {proj_desc}"
                else:
                    proj_desc_with_prefix = proj_desc
                work_descs.append(proj_desc_with_prefix)
                merged_count += 1
        resume["work_desc_tks"] = work_descs
        # Clear project_desc_tks — all content is now in work_desc_tks
        resume["project_desc_tks"] = []
        logger.info(f"Merged project descs into work_desc_tks: {merged_count} merged, {skipped_count} skipped (duplicate)")
    # --- Phase 4: Field completion ---
    required_fields = [
        "name_kwd", "gender_kwd", "phone_kwd", "email_tks",
        "position_name_tks", "school_name_tks", "major_tks",
    ]
    for field in required_fields:
        if field not in resume:
            if field.endswith("_tks"):
                resume[field] = []
            elif field.endswith("_int") or field.endswith("_flt"):
                resume[field] = 0
            else:
                resume[field] = ""

    # Clean internal marker fields (already handled in Phase 1, this is a safety fallback)
    resume.pop("_name_confidence", None)

    return resume