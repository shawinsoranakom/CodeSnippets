async def _fetch_report_detail(rpt: dict) -> dict | None:
        citation = rpt.get("citation", "")
        rpt_type = rpt.get("type", "")
        number = rpt.get("number")
        part = rpt.get("part", 1)

        if not number or not rpt_type:
            return None

        type_lower = rpt_type.lower()
        base = f"CRPT-{congress}{type_lower}{number}"

        if ",Part" in citation:
            pdf_url = f"https://www.congress.gov/{congress}/crpt/{type_lower}{number}/{base}-pt{part}.pdf"
        else:
            pdf_url = f"https://www.congress.gov/{congress}/crpt/{type_lower}{number}/{base}.pdf"

        detail_url = (
            f"{base_url}committee-report/{congress}/{rpt_type}/{number}"
            f"?format=json&api_key={api_key}"
        )
        title = citation
        issue_date = ""

        async with sem:
            try:
                detail = await amake_request(detail_url, timeout=20, **kwargs)
            except Exception:
                detail = None

        if isinstance(detail, dict):
            for cr in detail.get("committeeReports", []):
                title = cr.get("title") or citation
                issue_date = (cr.get("issueDate") or "")[:10]
                break

        if issue_date:
            title = f"[{issue_date}] {title}"

        return {
            "doc_type": "report",
            "citation": citation or None,
            "title": title,
            "congress": congress,
            "chamber": chamber.title(),
            "doc_url": pdf_url,
        }