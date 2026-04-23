def transform_data(
        query: CongressCommitteeInfoQueryParams,
        data: dict,
        **kwargs,
    ) -> CongressCommitteeInfoData:
        """Transform the raw data into a CongressCommitteeInfoData instance."""
        chamber = data.get("chamber", "")
        system_code = data.get("system_code", "")
        detail = data.get("detail", {})
        members = data.get("members", [])
        history = detail.get("history", [])
        name = ""

        for h in reversed(history):
            candidate = h.get("officialName") or h.get("libraryOfCongressName") or ""
            if candidate:
                name = candidate
                break

        if not name:
            name = system_code.upper()

        committee_type = detail.get("type", "")
        website = detail.get("committeeWebsiteUrl") or ""
        is_current = detail.get("isCurrent", True)
        update_date = (detail.get("updateDate") or "")[:10]
        reports_info = detail.get("reports") or {}
        bills_info = detail.get("bills") or {}
        nominations_info = detail.get("nominations") or {}
        comms_info = detail.get("communications") or {}
        subcommittees = detail.get("subcommittees") or []
        md = f"# {name}\n\n"
        meta_rows = [
            ("Chamber", chamber.title()),
            ("Type", committee_type),
            ("System Code", f"`{system_code}`"),
            ("Current", "Yes" if is_current else "No"),
            ("Last Updated", update_date),
        ]

        if website:
            meta_rows.append(("Website", f"[{website}]({website})"))

        md += "## Overview\n\n"
        md += "| Field | Value |\n|---|---|\n"

        for label, val in meta_rows:
            md += f"| {label} | {val} |\n"

        md += "\n## Activity Counts\n\n"
        md += "| Type | Count |\n|---|---|\n"

        for label, info in [
            ("Reports", reports_info),
            ("Bills Referred", bills_info),
            ("Nominations", nominations_info),
            ("Communications", comms_info),
        ]:
            if isinstance(info, dict):
                count = info.get("count", 0)

                if count:
                    md += f"| {label} | {count:,} |\n"

        if subcommittees:
            md += f"\n## Subcommittees ({len(subcommittees)})\n\n"

            for sub in subcommittees:
                sub_name = sub.get("name", "")
                sub_code = sub.get("systemCode", "")

                if sub_name:
                    md += f"- **{sub_name}** (`{sub_code}`)\n"

        if members:
            chair = [
                m
                for m in members
                if m.get("title", "").lower()
                in ("chair", "chairman", "chairwoman", "chairperson")
            ]
            ranking = [m for m in members if "ranking" in m.get("title", "").lower()]
            rest = [m for m in members if m not in chair and m not in ranking]
            md += f"\n## Members ({len(members)})\n\n"
            md += "| Name | Party | Title |\n|---|---|---|\n"

            for m in chair + ranking + rest:
                name_val = m.get("name", "Unknown")
                party = m.get("party", "")
                title = m.get("title") or "Member"
                md += f"| {name_val} | {party} | {title} |\n"
        else:
            md += "\n*Member data not available for this committee.*\n"

        if history:
            md += "\n## Historical Names\n\n"

            for h in history:
                official = h.get("officialName") or h.get("libraryOfCongressName") or ""
                start = (h.get("startDate") or "")[:10]
                end = (h.get("endDate") or "present")[:10]
                if official:
                    md += f"- {official} ({start} – {end})\n"

        return CongressCommitteeInfoData(
            markdown_content=md,
            raw_data=data,
        )