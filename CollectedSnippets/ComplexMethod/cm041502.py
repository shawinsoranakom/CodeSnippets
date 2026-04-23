def secretsmanager_http_list_secret_version_ids_val_res(
        res: requests.Response, secret_name: str, versions: json
    ) -> json:
        assert res.status_code == 200
        res_json: json = res.json()
        assert res_json["Name"] == secret_name
        res_versions: [json] = res_json["Versions"]
        assert len(res_versions) == len(versions)
        assert len({rv["VersionId"] for rv in res_versions}) == len(res_versions)
        assert len({v["VersionId"] for v in versions}) == len(versions)
        for version in versions:
            vs_in_res: [json] = list(
                filter(lambda rv: rv["VersionId"] == version["VersionId"], res_versions)
            )
            assert len(vs_in_res) == 1
            v_in_res = vs_in_res[0]
            assert v_in_res["VersionStages"] == version["VersionStages"]
        return res_json