def maybe_add_missing_fqns(results: NSResultsType) -> None:
    """
    If `fqn` entries are filled in for one of the models in `results`, copies
    them over to any models which do not have them filled out.

    A common use case benefitting from this is comparing a model prepared by
    quantization to a quantized model. In this case, the model prepared by
    quantization would have `fqn` entries, and the quantized model would not.
    """

    # Check in the first result to find any model with fqn entries defined.
    model_name_with_fqns = None
    for result_type_to_results in results.values():
        for model_name_to_results in result_type_to_results.values():
            for model_name, model_results in model_name_to_results.items():
                if len(model_results) > 0:
                    if model_results[0]["fqn"] is not None:
                        model_name_with_fqns = model_name
                        break
            break
        break

    if model_name_with_fqns:
        for result_type_to_results in results.values():
            for model_name_to_results in result_type_to_results.values():
                ref_model_results = model_name_to_results[model_name_with_fqns]
                for model_name, model_results in model_name_to_results.items():
                    if model_name == model_name_with_fqns:
                        continue

                    for i in range(len(model_results)):
                        fqn = ref_model_results[i]["fqn"]
                        model_results[i]["fqn"] = fqn