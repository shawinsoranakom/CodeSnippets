def test_list_assets_include_tags_variants_and_case(http, api_base, asset_factory, make_asset_bytes):
    t = ["models", "checkpoints", "unit-tests", "lf-include"]
    a = asset_factory("incvar_alpha.safetensors", [*t, "alpha"], {}, make_asset_bytes("iva"))
    asset_factory("incvar_beta.safetensors", [*t, "beta"], {}, make_asset_bytes("ivb"))

    # CSV + case-insensitive
    r1 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "UNIT-TESTS,LF-INCLUDE,alpha"},
        timeout=120,
    )
    b1 = r1.json()
    assert r1.status_code == 200
    names1 = [x["name"] for x in b1["assets"]]
    assert a["name"] in names1
    assert not any("beta" in x for x in names1)

    # Repeated query params for include_tags
    params_multi = [
        ("include_tags", "unit-tests"),
        ("include_tags", "lf-include"),
        ("include_tags", "alpha"),
    ]
    r2 = http.get(api_base + "/api/assets", params=params_multi, timeout=120)
    b2 = r2.json()
    assert r2.status_code == 200
    names2 = [x["name"] for x in b2["assets"]]
    assert a["name"] in names2
    assert not any("beta" in x for x in names2)

    # Duplicates and spaces in CSV
    r3 = http.get(
        api_base + "/api/assets",
        params={"include_tags": " unit-tests , lf-include , alpha , alpha "},
        timeout=120,
    )
    b3 = r3.json()
    assert r3.status_code == 200
    names3 = [x["name"] for x in b3["assets"]]
    assert a["name"] in names3