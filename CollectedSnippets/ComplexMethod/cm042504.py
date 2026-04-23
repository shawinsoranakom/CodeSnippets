def generate_dbc_dict() -> dict[str, str]:
  dbc_map = {}
  for platform in PLATFORMS.values():
    if platform != "MOCK":
      if Bus.pt in platform.config.dbc_dict:
        dbc_map[platform.name] = platform.config.dbc_dict[Bus.pt]
      elif Bus.main in platform.config.dbc_dict:
        dbc_map[platform.name] = platform.config.dbc_dict[Bus.main]
      elif Bus.party in platform.config.dbc_dict:
        dbc_map[platform.name] = platform.config.dbc_dict[Bus.party]
      else:
        raise ValueError("Unknown main type")

  for m in MIGRATION:
    if MIGRATION[m] in dbc_map:
      dbc_map[m] = dbc_map[MIGRATION[m]]

  return dbc_map