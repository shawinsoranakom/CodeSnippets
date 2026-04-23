def mark_coverage_acceptance_test(
    path_to_acceptance_metrics: str, coverage_collection: dict
) -> dict:
    """
    Iterates over all csv files in `path_to_acceptance_metrics` and updates the information in the `coverage_collection`
    dict about which API call was covered by the acceptance metrics

        { "service_name":
            {
                "operation_name_1": { "status_code": True},
                "operation_name2": {"status_code_1": False, "status_code_2": True}
            },
          "service_name_2": ....
        }

    If any API calls are identified, that have not been covered with the initial run, those will be collected separately.
    Normally, this should never happen, because acceptance tests should be a subset of integrations tests.
    Could, however, be useful to identify issues, or when comparing test runs locally.

    :param path_to_acceptance_metrics: path to the metrics
    :param coverage_collection: Dict with the coverage collection about the initial test integration run

    :returns:  dict with additional recorded coverage, only covered by the acceptance test suite
    """
    pathlist = Path(path_to_acceptance_metrics).rglob("*.csv")
    additional_tested = {}
    add_to_additional = False
    for path in pathlist:
        with open(path) as csv_obj:
            print(f"Processing acceptance test coverage metrics: {path}")
            csv_dict_reader = csv.DictReader(csv_obj)
            for metric in csv_dict_reader:
                service = metric.get("service")
                operation = metric.get("operation")
                response_code = metric.get("response_code")

                if service not in coverage_collection:
                    add_to_additional = True
                else:
                    service_details = coverage_collection[service]
                    if operation not in service_details:
                        add_to_additional = True
                    else:
                        operation_details = service_details.setdefault(operation, {})
                        if response_code not in operation_details:
                            add_to_additional = True
                        else:
                            operation_details[response_code] = True

                if add_to_additional:
                    service_details = additional_tested.setdefault(service, {})
                    operation_details = service_details.setdefault(operation, {})
                    if response_code not in operation_details:
                        operation_details[response_code] = True
                    add_to_additional = False

    return additional_tested