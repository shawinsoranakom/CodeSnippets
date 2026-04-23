def get_available_reporting_integrations():
    integrations = []
    if is_azureml_available() and not is_mlflow_available():
        integrations.append("azure_ml")
    if is_comet_available():
        integrations.append("comet_ml")
    if is_dagshub_available():
        integrations.append("dagshub")
    if is_dvclive_available():
        integrations.append("dvclive")
    if is_mlflow_available():
        integrations.append("mlflow")
    if is_neptune_available():
        integrations.append("neptune")
    if is_tensorboard_available():
        integrations.append("tensorboard")
    if is_wandb_available():
        integrations.append("wandb")
    if is_codecarbon_available():
        integrations.append("codecarbon")
    if is_clearml_available():
        integrations.append("clearml")
    if is_swanlab_available():
        integrations.append("swanlab")
    if is_trackio_available():
        integrations.append("trackio")
    if is_kubeflow_available():
        integrations.append("kubeflow")
    return integrations