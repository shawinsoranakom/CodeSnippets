async def get_all_series_ids(survey):
        """Get an asset in the FTP download folder of the two-letter survey code."""
        if survey in ["ch", "cs", "fw", "is", "nw", "oe", "yy"]:
            return
        data = await get_survey_asset(survey, "series")
        for col in ["series_title", "survey_name"]:
            if col not in data.columns:  # type: ignore
                data.loc[:, col] = None  # type: ignore
        codes = [d for d in data.columns if "code" in d and "periodicity" not in d]  # type: ignore
        ids = data.get(["series_id", "series_title"] + codes).copy()  # type: ignore

        if ids is None or ids.empty:
            return

        ids = ids.rename(columns={"footnote_codes": "footnote_code"})
        ids = ids.astype(str).replace({"nan": None, "''": None, "": None})

        ids["survey_name"] = SURVEY_NAMES.get(survey.upper(), None)
        ids = ids[ids.series_id.astype(str).str.startswith(survey.upper())]

        if ids is None or ids.empty:
            return

        # Get the code maps for the survey and convert the codes in the series table.
        code_map: dict = {}
        new_codes = [d.split("_")[0] for d in codes]

        for code in new_codes:
            code = "datatype" if code == "data" else code  # noqa
            code_dict: dict = {}
            code_data = await get_survey_asset(survey, code)
            if code_data is None or code_data.empty:
                continue
            code = (  # noqa
                "data_type" if code == "datatype" and survey == "ce" else code
            )
            code_data = code_data.rename(
                columns={
                    col: f"{code}_name"
                    for col in code_data.columns
                    if col in [f"{code}_text", f"{code}_title"]
                }
            )
            if f"{code}_code" in code_data.columns:
                if (
                    code_data.index.dtype == "object"
                    and code_data.get(f"{code}_name").isnull().all()  # type: ignore
                ):
                    code_data.loc[:, f"{code}_name"] = code_data.loc[
                        :, f"{code}_code"
                    ].copy()
                    code_data.loc[:, f"{code}_code"] = code_data.index.copy()  # type: ignore
                    code_data = code_data.reset_index(drop=True)
                code_dict = (
                    code_data.set_index(f"{code}_code")[[f"{code}_name"]]
                    .to_dict()
                    .get(f"{code}_name", code_dict)
                )
            else:
                code_dict = code_data.to_dict(orient="series")

            code_map[f"{code}_code"] = code_dict
            ids[f"{code}_code"] = [code_dict.get(d, d) for d in ids[f"{code}_code"]]

        # Footnotes may be comma-separated, so we need to expand them.
        if "footnote_code" in ids.columns:
            expanded_data = []
            for item in ids["footnote_code"]:
                if (
                    item
                    and isinstance(item, str)
                    and "," in item
                    and any(char.isdigit() for char in item)
                ):
                    expanded_data.append(
                        " ".join(
                            [
                                code_map["footnote_code"].get(sub_item, sub_item)
                                for sub_item in item.split(",")
                                if code_map["footnote_code"].get(sub_item) is not None
                            ]
                        )
                    )
                else:
                    expanded_data.append(item)
            ids["footnote_code"] = expanded_data

        ids = ids.replace({nan: None, "nan": None, "''": None}).to_dict(
            orient="records"
        )
        series_ids.extend(ids)
        series_codes.update({survey: code_map})