async def get_one(URL):
            """Get the observations for a single date."""
            response = await amake_request(URL)

            # If the response has no elements we return empty and try the next URL.
            # If all URLs return empty, it will raise in `transform_data`.
            if "elements" not in response:
                return

            res: list = []
            data: list = []
            # We use `res` to store the table and section elements
            # and to identify if observation values are returned.
            # We use `data` to store the observation values.
            # Only one scenario should unfold.
            for v in response.get("elements", {}).values():  # type: ignore
                if v and (v.get("type") == "section" or v.get("type") == "table"):
                    v["element_id"] = str(v["element_id"])
                    v["parent_id"] = str(v["parent_id"]) if v.get("parent_id") else None
                    v.pop("children", None)
                    v.pop("release_id", None)
                    res.append(v)
                elif (
                    "observation_value" in v
                    and v.get("observation_value") != "."
                    and v.get("type") != "header"
                ):
                    v["element_id"] = str(v["element_id"])
                    data.append(v)
            # When observation values are returned, we parse and collect the parent elements while flattening the data.
            if data:
                index_cols = ["line", "element_id", "parent_id"]
                df = DataFrame(data).dropna(how="all", axis=1)
                for index_col in index_cols.copy():
                    if index_col not in df.columns:
                        index_cols.remove(index_col)
                df = (
                    df.set_index(index_cols)
                    .sort_index()[
                        [
                            "level",
                            "series_id",
                            "name",
                            "observation_date",
                            "observation_value",
                        ]
                    ]
                    .reset_index()
                )
                df["parent_id"] = df.parent_id.astype(str)
                df["element_id"] = df.element_id.astype(str)
                df["observation_value"] = df.observation_value.str.replace(
                    ",", ""
                ).astype(float)

                if "line" in df.columns:
                    df["line"] = df.line.astype(int)

                # Some dates are in the format 'Jan 2021' and others are '2021-01-01'.
                def apply_date_format(x):
                    """Apply the date format."""
                    x = x.replace(" ", "-")
                    if x.startswith("Q"):
                        new_x = x.split("-")[-1]
                        q_dict = {
                            "Q1": "-03-31",
                            "Q2": "-06-30",
                            "Q3": "-09-30",
                            "Q4": "-12-31",
                        }
                        return new_x + q_dict[x.split("-")[0]]
                    try:
                        return to_datetime(x).date()
                    except ValueError:
                        try:
                            return to_datetime(x, format="%b-%Y").date()
                        except ValueError:
                            return x

                df["observation_date"] = df.observation_date.apply(apply_date_format)
                children = (
                    df.groupby("parent_id")["element_id"]
                    .apply(lambda x: x.sort_values().unique().tolist())
                    .to_dict()
                )
                children = {k: ",".join(v) for k, v in children.items()}
                df["children"] = df.element_id.map(children)
                new_index_cols = [
                    "line",
                    "element_id",
                    "children",
                    "parent_id",
                    "level",
                ]
                for index_col in new_index_cols.copy():
                    if index_col not in df.columns:
                        new_index_cols.remove(index_col)
                df = (
                    df.set_index(new_index_cols)
                    .sort_index()
                    .reset_index()
                    .replace({nan: None})
                )
                results.extend(df.to_dict("records"))
            # If no observation values are returned, we collect the unique element IDs for the user.
            elif res:
                for item in res:
                    if not any(r["element_id"] == item["element_id"] for r in results):
                        results.append(item)