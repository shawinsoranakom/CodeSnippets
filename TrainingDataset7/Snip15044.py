def list_resources_with_updates(
    date_since, resources=None, languages=None, verbosity=0
):
    api_token = get_api_token()
    project = "o:django:p:django"
    date_since_iso = date_since.isoformat().strip("Z") + "Z"
    if verbosity:
        print(f"\n== Starting list_resources_with_updates at {date_since_iso=}")

    if not languages:
        languages = [  # List languages using Transifex projects API.
            d["attributes"]["code"]
            for d in get_api_response(
                f"projects/{project}/languages", api_token, verbosity=verbosity
            )
        ]
    if verbosity > 1:
        print(f"\n=== Languages to process: {languages=}")

    if not resources:
        resources = [  # List resources using Transifex resources API.
            d["attributes"]["slug"]
            for d in get_api_response(
                "resources",
                api_token,
                params={"filter[project]": project},
                verbosity=verbosity,
            )
        ]
    else:
        resources = [_tx_resource_slug_for_name(r) for r in resources]
    if verbosity > 1:
        print(f"\n=== Resources to process: {resources=}")

    resource_lang_changed = defaultdict(list)
    for lang, resource in product(languages, resources):
        if verbosity:
            print(f"\n=== Getting data for: {lang=} {resource=} {date_since_iso=}")
        data = get_api_response(
            "resource_translations",
            api_token,
            params={
                "filter[resource]": f"{project}:r:{resource}",
                "filter[language]": f"l:{lang}",
                "filter[date_translated][gt]": date_since_iso,
            },
            verbosity=verbosity,
        )
        local_resource = resource.replace("contrib-", "", 1)
        local_lang = lang  # XXX: LANG_OVERRIDES.get(lang, lang)
        if data:
            resource_lang_changed[local_resource].append(local_lang)
            if verbosity > 2:
                fname = f"{local_resource}-{local_lang}.json"
                with open(fname, "w") as f:
                    f.write(json.dumps(data, sort_keys=True, indent=2))
                print(f"==== Stored full data JSON in: {fname}")
        if verbosity > 1:
            print(f"==== Result for {local_resource=} {local_lang=}: {len(data)=}")

    return resource_lang_changed