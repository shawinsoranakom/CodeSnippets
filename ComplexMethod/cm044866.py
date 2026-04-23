def _get_name_params(model_path, model_hash):
    data = load_data()
    flag = False
    ModelName = model_path
    for type in list(data):
        for model in list(data[type][0]):
            for i in range(len(data[type][0][model])):
                if str(data[type][0][model][i]["hash_name"]) == model_hash:
                    flag = True
                elif str(data[type][0][model][i]["hash_name"]) in ModelName:
                    flag = True

                if flag:
                    model_params_auto = data[type][0][model][i]["model_params"]
                    param_name_auto = data[type][0][model][i]["param_name"]
                    if type == "equivalent":
                        return param_name_auto, model_params_auto
                    else:
                        flag = False
    return param_name_auto, model_params_auto