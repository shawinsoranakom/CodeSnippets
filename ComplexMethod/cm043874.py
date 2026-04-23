def open_asset(asset: str) -> Union["DataFrame", dict]:
    """Open a static file asset for series IDs or code maps."""
    # pylint: disable=import-outside-toplevel
    import os  # noqa
    import json
    from importlib.resources import files
    from pathlib import Path
    from numpy import nan
    from openbb_core.app.model.abstract.error import OpenBBError
    from pandas import read_csv

    if ".xz" not in asset and "series" in asset:
        asset = asset + ".xz"
    elif ".json" not in asset and "codes" in asset:
        asset = asset + ".json"
    elif ".json" in asset or ".xz" in asset:
        pass
    else:
        raise OpenBBError(f"Asset '{asset}' not supported. Expected .json or .xz file.")

    assets_path = Path(str(files("openbb_bls").joinpath("assets")))

    if not os.path.exists(assets_path.joinpath(asset)):
        raise OpenBBError(f"Asset '{asset}' not found.")

    if asset.endswith(".json"):
        with open(assets_path.joinpath(asset)) as f:
            return json.load(f)
    else:
        with open(assets_path.joinpath(asset), "rb") as f:
            df = read_csv(f, compression="xz", low_memory=False, dtype="str")
        return df.replace({nan: None, "nan": None, "''": None}).dropna(
            how="all", axis=1
        )