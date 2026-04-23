def build_geoip_path(*parts):
    return pathlib.Path(__file__).parent.joinpath("data/geoip2", *parts).resolve()