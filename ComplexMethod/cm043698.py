def transform_data(
        query: CongressAmendmentsQueryParams, data: list, **kwargs: Any
    ) -> list[CongressAmendmentsData]:
        """Transform raw data into CongressAmendmentsData models."""
        transformed_data: list[CongressAmendmentsData] = []

        for amendment in sorted(
            data,
            key=lambda x: x.get("latestAction", {}).get("actionDate")
            or x.get("updateDate"),
            reverse=query.sort_by == "desc",
        ):
            latest_action = amendment.pop("latestAction", {})

            if latest_action:
                amendment["latest_action_date"] = latest_action.get("actionDate")
                amendment["latest_action_time"] = latest_action.get("actionTime")
                amendment["latest_action"] = latest_action.get("text")

            amended_bill = amendment.pop("amendedBill", {}) or {}

            if amended_bill:
                bill_type = amended_bill.get("type", "")
                bill_number = amended_bill.get("number", "")
                amendment["amended_bill"] = f"{bill_type} {bill_number}".strip() or None
                amendment["amended_bill_title"] = amended_bill.get("title") or None

            amended_amendment = amendment.pop("amendedAmendment", {}) or {}

            if amended_amendment and not amendment.get("amended_bill"):
                aa_type = amended_amendment.get("type", "")
                aa_number = amended_amendment.get("number", "")
                amendment["amended_bill"] = (
                    f"Amdt. {aa_type} {aa_number}".strip() or None
                )

            sponsors = amendment.pop("sponsors", []) or []

            if sponsors:
                amendment["sponsor"] = sponsors[0].get("fullName") or None

            if submitted := amendment.pop("submittedDate", None):
                amendment["submitted_date"] = submitted[:10]

            if update_date := amendment.get("updateDate"):
                amendment["updateDate"] = update_date[:10]

            transformed_data.append(CongressAmendmentsData(**amendment))

        return transformed_data