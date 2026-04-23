def main_evaluation(
    p,
    default_evaluation_params_fn,
    validate_data_fn,
    evaluate_method_fn,
    show_result=True,
    per_sample=True,
):
    """
    This process validates a method, evaluates it and if it succeed generates a ZIP file with a JSON entry for each sample.
    Params:
    p: Dictionary of parameters with the GT/submission locations. If None is passed, the parameters send by the system are used.
    default_evaluation_params_fn: points to a function that returns a dictionary with the default parameters used for the evaluation
    validate_data_fn: points to a method that validates the correct format of the submission
    evaluate_method_fn: points to a function that evaluated the submission and return a Dictionary with the results
    """
    evalParams = default_evaluation_params_fn()
    if "p" in p.keys():
        evalParams.update(
            p["p"] if isinstance(p["p"], dict) else json.loads(p["p"][1:-1])
        )

    resDict = {"calculated": True, "Message": "", "method": "{}", "per_sample": "{}"}
    try:
        # validate_data_fn(p['g'], p['s'], evalParams)
        evalData = evaluate_method_fn(p["g"], p["s"], evalParams)
        resDict.update(evalData)

    except Exception as e:
        traceback.print_exc()
        resDict["Message"] = str(e)
        resDict["calculated"] = False

    if "o" in p:
        if not os.path.exists(p["o"]):
            os.makedirs(p["o"])

        resultsOutputname = p["o"] + "/results.zip"
        outZip = zipfile.ZipFile(resultsOutputname, mode="w", allowZip64=True)

        del resDict["per_sample"]
        if "output_items" in resDict.keys():
            del resDict["output_items"]

        outZip.writestr("method.json", json.dumps(resDict))

    if not resDict["calculated"]:
        if show_result:
            sys.stderr.write("Error!\n" + resDict["Message"] + "\n\n")
        if "o" in p:
            outZip.close()
        return resDict

    if "o" in p:
        if per_sample == True:
            for k, v in evalData["per_sample"].items():
                outZip.writestr(k + ".json", json.dumps(v))

            if "output_items" in evalData.keys():
                for k, v in evalData["output_items"].items():
                    outZip.writestr(k, v)

        outZip.close()

    if show_result:
        sys.stdout.write("Calculated!")
        sys.stdout.write(json.dumps(resDict["method"]))

    return resDict