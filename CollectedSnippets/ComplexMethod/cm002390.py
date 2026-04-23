def build_failed_report(results, include_warning=True):
    failed_results = {}
    for config_name in results:
        if "error" in results[config_name]:
            if config_name not in failed_results:
                failed_results[config_name] = {}
            failed_results[config_name] = {"error": results[config_name]["error"]}

        if include_warning and "warnings" in results[config_name]:
            if config_name not in failed_results:
                failed_results[config_name] = {}
            failed_results[config_name]["warnings"] = results[config_name]["warnings"]

        if "pytorch" not in results[config_name]:
            continue
        for arch_name in results[config_name]["pytorch"]:
            if "error" in results[config_name]["pytorch"][arch_name]:
                if config_name not in failed_results:
                    failed_results[config_name] = {}
                if "pytorch" not in failed_results[config_name]:
                    failed_results[config_name]["pytorch"] = {}
                if arch_name not in failed_results[config_name]["pytorch"]:
                    failed_results[config_name]["pytorch"][arch_name] = {}
                error = results[config_name]["pytorch"][arch_name]["error"]
                failed_results[config_name]["pytorch"][arch_name]["error"] = error

    return failed_results