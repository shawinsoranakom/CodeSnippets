def transform_data(
        query: CongressAmendmentInfoQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> CongressAmendmentInfoData:
        """Transform the data into the model."""
        number = data.get("number", "")
        amendment_type = data.get("type", "")
        congress = data.get("congress", "")
        description = data.get("description", "")
        purpose = data.get("purpose", "")
        header = (
            description or purpose or f"Amendment {congress} {amendment_type} {number}"
        )

        markdown_content = f"# {header}\n\n"
        if purpose and purpose != description:
            markdown_content += f"> {purpose}\n\n"
        markdown_content += f"- **Congress**: {congress}\n"
        markdown_content += f"- **Number**: {number}\n"
        markdown_content += f"- **Type**: {amendment_type}\n"
        markdown_content += f"- **Chamber**: {data.get('chamber', '')}\n"

        submitted_at = data.get("submittedDate") or data.get("proposedDate")
        if submitted_at:
            markdown_content += f"- **Submitted**: {submitted_at}\n"

        markdown_content += f"- **Last Updated**: {data.get('updateDate', '')}\n"

        latest_action = data.get("latestAction", {})
        if latest_action:
            markdown_content += (
                f"- **Latest Action**: {latest_action.get('actionDate', '')} - "
                f"{latest_action.get('text', '')}\n"
            )

        amended_bill = data.get("amendedBill", {})
        if amended_bill:
            bill_congress = amended_bill.get("congress", "")
            bill_type = amended_bill.get("type", "")
            bill_number = amended_bill.get("number", "")
            bill_title = amended_bill.get("title", "")
            markdown_content += (
                f"\n### Amended Bill\n\n"
                f"- **{bill_congress} {bill_type} {bill_number}**: {bill_title}\n"
            )

        amended_amendment = data.get("amendedAmendment", {})
        if amended_amendment:
            aa_congress = amended_amendment.get("congress", "")
            aa_type = amended_amendment.get("type", "")
            aa_number = amended_amendment.get("number", "")
            markdown_content += (
                f"\n### Amends Amendment\n\n"
                f"- **{aa_congress} {aa_type} {aa_number}**\n"
            )

        sponsors = data.get("sponsors", [])
        if sponsors:
            markdown_content += "\n### Sponsors\n\n"
            for sponsor in sponsors:
                markdown_content += f"- **{sponsor.get('fullName', '')}**"
                if sponsor.get("party"):
                    markdown_content += f" ({sponsor.get('party', '')})"
                markdown_content += "\n"

        cosponsors = data.get("cosponsors", {})
        if isinstance(cosponsors, list) and cosponsors:
            markdown_content += "\n### Cosponsors\n\n"
            for cosponsor in cosponsors:
                cosponsor_name = cosponsor.get("fullName", "")
                markdown_content += f"- **{cosponsor_name}**"
                if cosponsor.get("party"):
                    markdown_content += f" ({cosponsor.get('party', '')})"
                markdown_content += "\n"
        elif isinstance(cosponsors, dict) and cosponsors.get("count", 0):
            markdown_content += (
                f"\n### Cosponsors\n\n- **Count**: {cosponsors['count']}\n"
            )

        text_versions = data.get("textVersions", [])
        if text_versions and isinstance(text_versions, list):
            markdown_content += "\n### Text Versions\n\n"
            for version in text_versions:
                version_date = version.get("date", "")
                version_type = version.get("type", "")
                markdown_content += f"- **{version_type}** ({version_date})\n"
                for fmt in version.get("formats", []):
                    fmt_type = fmt.get("type", "")
                    fmt_url = fmt.get("url", "")
                    markdown_content += f"  - [{fmt_type}]({fmt_url})\n"

        actions = data.get("actions", [])
        if actions and isinstance(actions, list):
            markdown_content += "\n### Actions\n\n"
            for action in actions:
                action_date = action.get("actionDate", "")
                action_text = action.get("text", "")
                action_type = action.get("type", "")
                markdown_content += f"\n- **{action_date}**: ({action_type})"
                markdown_content += f"\n  - {action_text}"

        return CongressAmendmentInfoData(
            markdown_content=markdown_content, raw_data=data
        )