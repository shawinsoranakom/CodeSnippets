def dsn(settings_dict):
    if settings_dict["PORT"]:
        host = settings_dict["HOST"].strip() or "localhost"
        return Database.makedsn(host, int(settings_dict["PORT"]), settings_dict["NAME"])
    return settings_dict["NAME"]