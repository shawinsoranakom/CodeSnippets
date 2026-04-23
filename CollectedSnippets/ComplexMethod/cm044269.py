def to_dataframe(  # noqa: PLR0912
        self,
        index: str | None | None = "date",
        sort_by: str | None = None,
        ascending: bool | None = None,
    ) -> "DataFrame":
        """Convert results field to Pandas DataFrame.

        Supports converting creating Pandas DataFrames from the following
        serializable data formats:

        - List[BaseModel]
        - List[Dict]
        - List[List]
        - List[str]
        - List[int]
        - List[float]
        - Dict[str, Dict]
        - Dict[str, List]
        - Dict[str, BaseModel]

        Other supported formats:
        - str

        Parameters
        ----------
        index : Optional[str]
            Column name to use as index.
        sort_by : Optional[str]
            Column name to sort by.
        ascending: Optional[bool]
            Sort by ascending for each column specified in `sort_by`.

        Returns
        -------
        DataFrame
            Pandas DataFrame.
        """
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame, Series, concat  # noqa
        from openbb_core.app.utils import basemodel_to_df  # noqa

        def is_list_of_basemodel(items: list[T] | T) -> bool:
            return isinstance(items, list) and all(
                isinstance(item, BaseModel) for item in items
            )

        if self.results is None or not self.results:
            raise OpenBBError("Results not found.")

        if isinstance(self.results, DataFrame):
            return self.results

        try:
            res = self.results
            df = None
            sort_columns = True

            # BaseModel
            if isinstance(res, BaseModel):
                res_dict = res.model_dump(  # pylint: disable=no-member
                    exclude_unset=True, exclude_none=True
                )
                # Model is serialized as a dict[str, list] or list[dict]
                if (
                    (
                        isinstance(res_dict, dict)
                        and res_dict
                        and all(isinstance(v, list) for v in res_dict.values())
                    )
                    or isinstance(res_dict, list)
                    and all(isinstance(item, dict) for item in res_dict)
                ):
                    df = DataFrame(res_dict)
                    sort_columns = False
                else:
                    series = Series(res_dict, name=res.__class__.__name__)
                    df = series.to_frame().reset_index()
                    sort_columns = False

            # Dict[str, Any]
            elif isinstance(res, dict):
                try:
                    df = DataFrame.from_dict(res).T
                except ValueError:
                    try:
                        df = DataFrame.from_dict(res, orient="index")
                    except ValueError:
                        series = Series(res, name="values")
                        df = series.to_frame().reset_index()
                sort_columns = False

            # List[Dict]
            elif isinstance(res, list) and len(res) == 1 and isinstance(res[0], dict):
                r = res[0]
                dict_of_df = {}

                for k, v in r.items():
                    # Dict[str, List[BaseModel]]
                    if is_list_of_basemodel(v):
                        dict_of_df[k] = basemodel_to_df(v, index)
                        sort_columns = False
                    # Dict[str, Any]
                    else:
                        dict_of_df[k] = DataFrame(v)

                df = concat(dict_of_df, axis=1)

            # List[BaseModel]
            elif is_list_of_basemodel(res):
                dt: list[Data] | Data = res  # type: ignore
                r = dt[0] if isinstance(dt, list) and len(dt) == 1 else None  # type: ignore
                if r and all(
                    prop.get("type") == "array" for prop in r.model_json_schema()["properties"].values()  # type: ignore
                ):
                    sort_columns = False
                    df = DataFrame(r.model_dump(exclude_unset=True, exclude_none=True))  # type: ignore
                else:
                    df = basemodel_to_df(dt, index)
                    sort_columns = False
            # str
            elif isinstance(res, str):
                df = DataFrame([res])
            # List[List | str | int | float] | Dict[str, Dict | List | BaseModel]
            else:
                try:
                    df = DataFrame(res)  # type: ignore[call-overload]
                except ValueError:
                    if isinstance(res, dict):
                        df = DataFrame([res])

            if df is None:
                raise OpenBBError("Unsupported data format.")

            # Set index, if any
            if index is not None and index in df.columns:
                df.set_index(index, inplace=True)

            # Drop columns that are all NaN, but don't rearrange columns
            if sort_columns:
                df.sort_index(axis=1, inplace=True)
            df = df.dropna(axis=1, how="all")

            # Sort by specified column
            if sort_by:
                df.sort_values(
                    by=sort_by,
                    ascending=ascending if ascending is not None else True,
                    inplace=True,
                )

        except OpenBBError as e:
            raise e
        except ValueError as ve:
            raise OpenBBError(
                f"ValueError: {ve}. Ensure the data format matches the expected format."
            ) from ve
        except TypeError as te:
            raise OpenBBError(
                f"TypeError: {te}. Check the data types in your results."
            ) from te
        except Exception as ex:
            raise OpenBBError(f"An unexpected error occurred: {ex}") from ex

        return df