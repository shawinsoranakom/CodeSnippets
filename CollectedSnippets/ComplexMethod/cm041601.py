def do_get_outdated_snapshots(path: str):
        if not path.endswith("/"):
            path = f"{path}/"
        for file in os.listdir(path):
            if os.path.isdir(f"{path}{file}") and check_sub_directories:
                do_get_outdated_snapshots(f"{path}{file}")
            elif file.endswith(".validation.json"):
                with open(f"{path}{file}") as f:
                    json_content: dict = json.load(f)
                    for name, recorded_snapshot_data in json_content.items():
                        recorded_date = recorded_snapshot_data.get("last_validated_date")
                        date = datetime.datetime.fromisoformat(recorded_date)
                        if date.timestamp() < date_limit:
                            outdated_snapshot_data = {}
                            if show_date:
                                outdated_snapshot_data["last_validation_date"] = recorded_date
                            if combine_parametrized:
                                # change parametrized tests of the form <mytest[param_value]> to just <mytest>
                                name = name.split("[")[0]
                            outdated_snapshots[name] = outdated_snapshot_data