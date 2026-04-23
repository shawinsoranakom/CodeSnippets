def extend_logger_results_with_comparison(
    results: NSResultsType,
    model_name_1: str,
    model_name_2: str,
    comparison_fn: Callable[[torch.Tensor, torch.Tensor], torch.Tensor],
    comparison_name: str,
) -> None:
    """
    Compares the logged values from `model_name_2` against the corresponding
    values in `model_name_1`, using `comparison_fn`. Records the result
    in `model_name_2`'s results under `comparison_name`. Modifies `results` inplace.

    Args:
        results: the result data structure from `extract_logger_info` or
          `extract_shadow_logger_info`.
        model_name_1: string name of model 1
        model_name_2: string name of model 2
        comparison_fn: function to compare two Tensors
        comparison_name: string name of model to use for
          layer names in the output
    """
    for results_type_to_results in results.values():
        for model_name_to_results in results_type_to_results.values():
            if model_name_1 not in model_name_to_results:
                raise AssertionError(f"{model_name_1} not found in results")
            if model_name_2 not in model_name_to_results:
                raise AssertionError(f"{model_name_2} not found in results")

            results_1 = model_name_to_results[model_name_1]
            results_2 = model_name_to_results[model_name_2]

            for result_2 in results_2:
                index_within_arg_2 = result_2["index_within_arg"]
                index_of_arg_2 = result_2["index_of_arg"]
                # find corresponding result_1
                result_1 = None
                for cur_result_1 in results_1:
                    index_within_arg_1 = cur_result_1["index_within_arg"]
                    index_of_arg_1 = cur_result_1["index_of_arg"]
                    if (index_within_arg_1 == index_within_arg_2) and (
                        index_of_arg_1 == index_of_arg_2
                    ):
                        result_1 = cur_result_1
                        break
                if result_1 is None:
                    raise AssertionError("Expected result_1 to be not None")

                values_1 = result_1["values"]
                values_2 = result_2["values"]
                result_2[comparison_name] = []
                for value_1, value_2 in zip(values_1, values_2):
                    comparison_result = comparison_fn(value_1, value_2)
                    result_2[comparison_name].append(comparison_result)