def transform_data(  # pylint: disable=R0912,R0914  # noqa: PLR0912,PLR0914
        query: CongressBillInfoQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> CongressBillInfoData:
        """Transform the data into the model."""
        # pylint: disable=import-outside-toplevel
        import re

        # Regex to strip HTML tags
        html_tag_regex = re.compile(r"<[^>]+>")

        # Regex to match HTML list items
        li_regex = re.compile(r"<li[^>]*>(.*?)</li>", re.DOTALL | re.IGNORECASE)
        ul_regex = re.compile(r"<ul[^>]*>(.*?)</ul>", re.DOTALL | re.IGNORECASE)
        ol_regex = re.compile(r"<ol[^>]*>(.*?)</ol>", re.DOTALL | re.IGNORECASE)
        strong_tag_regex = re.compile(
            r"<strong>(.*?)</strong>", re.DOTALL | re.IGNORECASE
        )
        p_tag_regex = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)

        def html_to_markdown(text: str) -> str:
            """Convert HTML content to Markdown format."""
            # Extract the first <strong> tag inside a <p> as the title, if present
            title = ""
            paragraphs = p_tag_regex.findall(text)
            if paragraphs:
                first_p = paragraphs[0]
                strong_match = strong_tag_regex.search(first_p)
                if strong_match:
                    title = strong_match.group(1).strip()
                    # Remove the first <p><strong>...</strong></p> from text
                    text = text.replace(f"<p><strong>{title}</strong></p>", "", 1)
                    text = text.lstrip()
                    if text.startswith(title):
                        text = text[len(title) :].lstrip()

            # Convert unordered lists
            def ul_replacer(match):
                """Replace <ul> with Markdown format."""
                items = li_regex.findall(match.group(1))
                return "\n" + "\n".join(
                    f"- {html_tag_regex.sub('', item).strip()}" for item in items
                )

            # Convert ordered lists
            def ol_replacer(match):
                """Replace <ol> with Markdown format."""
                items = li_regex.findall(match.group(1))
                return "\n" + "\n".join(
                    f"1. {html_tag_regex.sub('', item).strip()}" for item in items
                )

            text = ul_regex.sub(ul_replacer, text)
            text = ol_regex.sub(ol_replacer, text)
            text = html_tag_regex.sub("", text)
            text = text.strip()

            if title:
                return f"**{title}**\n\n{text.replace(title.strip(), '').strip()}"

            return text

        markdown_content = f"""## {data.get("title")}

- **Congress**: {data.get("congress")}
- **Bill Number**: {data.get("number")}
- **Type**: {data.get("type")}
- **Chamber**: {data.get("originChamber")}
- **Introduced**: {data.get("introducedDate")}
- **Last Updated**: {data.get("updateDate", {})}
- **Last Action**: {data.get("latestAction", {}).get("actionDate")} - {data.get("latestAction", {}).get("text", "")}
"""
        policy_area = data.get("policyArea", {}).get("name", "")
        if policy_area:
            markdown_content += f"\n- **Policy Area**: {policy_area}"

        related_bills = data.get("relatedBills", [])
        if related_bills:
            markdown_content += "\n\n### Related Bills\n\n"
            for bill in related_bills:
                bill_number = bill.get("number", "")
                bill_type = bill.get("type", "")
                bill_congress = bill.get("congress", "")
                bill_title = bill.get("title", "")
                latest_action = bill.get("latestAction", {})
                markdown_content += (
                    f"\n- **{bill_congress} {bill_type} {bill_number}: {bill_title}**\n"
                )
                if latest_action:
                    action_date = latest_action.get("actionDate", "")
                    action_text = latest_action.get("text", "")
                    markdown_content += (
                        f"  - **Last Action**: {action_date} - {action_text}\n"
                    )

                relationship = bill.get("relationshipDetails", [])

                if relationship:
                    for rel in relationship:
                        rel_type = rel.get("type", "")
                        rel_description = rel.get("identifiedBy", "")
                        markdown_content += f"\n  - **Relationship**: {rel_type}\n"
                        markdown_content += (
                            f"    - **Identified By**: {rel_description}\n"
                        )

        summaries = data.get("summaries", [])
        if summaries:
            markdown_content += "\n\n### Summaries\n\n"
            for summary in summaries:
                summary_text = html_to_markdown(summary.get("text", ""))
                markdown_content += f"\n{summary_text}\n\n"

        subjects = data.get("subjects", [])
        if subjects:
            markdown_content += "\n\n### Subjects\n\n"
            for subject in subjects:
                markdown_content += f"\n  - **{subject.get('name', '')}** ({subject.get('updateDate', '')})"

        sponsors = data.get("sponsors", [])
        if sponsors:
            markdown_content += "\n\n### Sponsors\n\n"
            for sponsor in sponsors:
                markdown_content += f"\n  - **{sponsor.get('fullName', '')}**"

        cosponsors = data.get("cosponsors", [])
        if cosponsors:
            markdown_content += "\n\n### Cosponsors\n\n"
            for cosponsor in cosponsors:
                cosponsor_name = cosponsor.get("fullName", "")
                is_original = cosponsor.get("isOriginalCosponsor", False)
                if is_original:
                    cosponsor_name += " (Original Cosponsor)"
                markdown_content += f"\n  - **{cosponsor_name}** ({cosponsor.get('sponsorshipDate', '')})"

        titles = data.get("titles", [])
        if titles:
            markdown_content += "\n\n### Titles\n\n"
            for title in titles:
                title_text = title.get("title", "")
                markdown_content += f"\n- **{title_text}**\n"
                title_type = title.get("type", "")

                if title_type:
                    markdown_content += f"  - **Type**: {title_type}\n"

                chamber = title.get("chamberName", "")

                if chamber:
                    markdown_content += f"  - **Chamber**: {chamber}\n"

                bill_text_version_name = title.get("billTextVersionName", "")

                if bill_text_version_name:
                    markdown_content += (
                        f"  - **Bill Text Version**: {bill_text_version_name}\n"
                    )

                markdown_content += (
                    f"  - **Last Updated**: {title.get('updateDate', '')}\n"
                )

        committees = data.get("committees", [])
        if committees:
            markdown_content += "\n\n### Committees\n\n"
            for committee in committees:
                committee_name = committee.get("name", "")
                committee_chamber = committee.get("chamber", "")

                if committee_chamber:
                    markdown_content += f"- **{committee_name} - {committee_chamber} ({committee.get('type')})**\n"
                else:
                    markdown_content += f"- **{committee_name}**\n"

                activities = committee.get("activities", [])
                if activities:
                    for activity in activities:
                        markdown_content += f"  - {activity.get('name', '')} ({activity.get('date', '')})\n"

                subcommittees = committee.get("subcommittees", [])
                if subcommittees:
                    markdown_content += "  - **Subcommittees**:\n"
                    for subcommittee in subcommittees:
                        subcommittee_name = subcommittee.get("name", "")
                        markdown_content += f"    - **{subcommittee_name}**\n"
                        activities = subcommittee.get("activities", [])
                        if activities:
                            for activity in activities:
                                markdown_content += f"      - {activity.get('name', '')} ({activity.get('date', '')})\n"

        actions = data.get("actions", [])
        if actions:
            markdown_content += "\n\n### Actions\n\n"
            for action in actions:
                action_date = action.get("actionDate", "")
                action_text = action.get("text", "")
                action_type = action.get("type", "")
                markdown_content += f"\n- **{action_date}**: ({action_type})"
                markdown_content += f"\n  - {action_text}"

        return CongressBillInfoData(markdown_content=markdown_content, raw_data=data)