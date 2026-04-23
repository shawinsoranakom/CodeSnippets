def process_test(test_name: str, test_data: dict):
            result_group = grouped_success_values[f"{label}|{test_name}"]

            if "tests" in test_data:
                logger.debug(f"{test_name} is a test suite")

                # Test suite
                suite_attempted = any(
                    test["metrics"]["attempted"] for test in test_data["tests"].values()
                )
                logger.debug(f"suite_attempted: {suite_attempted}")
                if not suite_attempted:
                    return

                if test_name not in test_names:
                    test_names.append(test_name)

                if test_data["metrics"]["percentage"] == 0:
                    result_indicator = "❌"
                else:
                    highest_difficulty = test_data["metrics"]["highest_difficulty"]
                    result_indicator = {
                        "interface": "🔌",
                        "novice": "🌑",
                        "basic": "🌒",
                        "intermediate": "🌓",
                        "advanced": "🌔",
                        "hard": "🌕",
                    }[highest_difficulty]

                logger.debug(f"result group: {result_group}")
                logger.debug(f"runs_per_label: {runs_per_label[label]}")
                if len(result_group) + 1 < runs_per_label[label]:
                    result_group.extend(
                        ["❔"] * (runs_per_label[label] - len(result_group) - 1)
                    )
                result_group.append(result_indicator)
                logger.debug(f"result group (after): {result_group}")

                if granular:
                    for test_name, test in test_data["tests"].items():
                        process_test(test_name, test)
                return

            test_metrics = test_data["metrics"]
            result_indicator = "❔"

            if "attempted" not in test_metrics:
                return
            elif test_metrics["attempted"]:
                if test_name not in test_names:
                    test_names.append(test_name)

                # Handle old format (success: bool) and new (success_percentage)
                if "success" in test_metrics:
                    success_value = test_metrics["success"]
                elif "success_percentage" in test_metrics:
                    success_value = test_metrics["success_percentage"] >= 100.0
                else:
                    success_value = False
                result_indicator = {True: "✅", False: "❌"}[success_value]

            if len(result_group) + 1 < runs_per_label[label]:
                result_group.extend(
                    ["  "] * (runs_per_label[label] - len(result_group) - 1)
                )
            result_group.append(result_indicator)