def export_data(
    export_type: str,
    dir_path: str,
    func_name: str,
    df: pd.DataFrame = pd.DataFrame(),
    sheet_name: str | None = None,
    figure: Optional["OpenBBFigure"] = None,
    margin: bool = True,
) -> None:
    """Export data to a file.

    Parameters
    ----------
    export_type : str
        Type of export between: csv,json,xlsx,xls
    dir_path : str
        Path of directory from where this function is called
    func_name : str
        Name of the command that invokes this function
    df : pd.Dataframe
        Dataframe of data to save
    sheet_name : str
        If provided.  The name of the sheet to save in excel file
    figure : Optional[OpenBBFigure]
        Figure object to save as image file
    margin : bool
        Automatically adjust subplot parameters to give specified padding.
    """
    if export_type:
        saved_path = compose_export_path(func_name, dir_path).resolve()
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        for exp_type in export_type.split(","):
            # In this scenario the path was provided, e.g. --export pt.csv, pt.jpg
            if "." in exp_type:
                saved_path = saved_path.with_name(exp_type)
            # In this scenario we use the default filename
            else:
                if ".OpenBB_openbb_cli" in saved_path.name:
                    saved_path = saved_path.with_name(
                        saved_path.name.replace(".OpenBB_openbb_cli", "OpenBBCLI")
                    )
                saved_path = saved_path.with_suffix(f".{exp_type}")

            exists, overwrite = False, False
            is_xlsx = exp_type.endswith("xlsx")
            if sheet_name is None and is_xlsx or not is_xlsx:
                exists, overwrite = ask_file_overwrite(saved_path)

            if exists and not overwrite:
                existing = len(list(saved_path.parent.glob(saved_path.stem + "*")))
                saved_path = saved_path.with_stem(f"{saved_path.stem}_{existing + 1}")

            df = df.replace(
                {
                    r"\[yellow\]": "",
                    r"\[/yellow\]": "",
                    r"\[green\]": "",
                    r"\[/green\]": "",
                    r"\[red\]": "",
                    r"\[/red\]": "",
                    r"\[magenta\]": "",
                    r"\[/magenta\]": "",
                },
                regex=True,
            )

            if exp_type.endswith("csv"):
                df.to_csv(saved_path)
            elif exp_type.endswith("json"):
                df.reset_index(drop=True, inplace=True)
                df.to_json(saved_path)
            elif exp_type.endswith("xlsx"):
                # since xlsx does not support datetimes with timezones we need to remove it
                df = remove_timezone_from_dataframe(df)

                if sheet_name is None:  # noqa: SIM223
                    df.to_excel(
                        saved_path,
                        index=True,
                        header=True,
                    )
                else:
                    save_to_excel(df, saved_path, sheet_name)

            elif saved_path.suffix in [".jpg", ".png"]:
                if figure is None:
                    session.console.print("No plot to export.")
                    continue
                figure.show(export_image=saved_path, margin=margin)
            else:
                session.console.print("Wrong export file specified.")
                continue

            if saved_path.exists():
                session.console.print(f"Saved file: {saved_path}")
            else:
                session.console.print(f"Failed to save file: {saved_path}")

        if figure is not None:
            figure._exported = True