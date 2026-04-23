def model_sampling(model_config, model_type):
    s = comfy.model_sampling.ModelSamplingDiscrete

    if model_type == ModelType.EPS:
        c = comfy.model_sampling.EPS
    elif model_type == ModelType.V_PREDICTION:
        c = comfy.model_sampling.V_PREDICTION
    elif model_type == ModelType.V_PREDICTION_EDM:
        c = comfy.model_sampling.V_PREDICTION
        s = comfy.model_sampling.ModelSamplingContinuousEDM
    elif model_type == ModelType.FLOW:
        c = comfy.model_sampling.CONST
        s = comfy.model_sampling.ModelSamplingDiscreteFlow
    elif model_type == ModelType.STABLE_CASCADE:
        c = comfy.model_sampling.EPS
        s = comfy.model_sampling.StableCascadeSampling
    elif model_type == ModelType.EDM:
        c = comfy.model_sampling.EDM
        s = comfy.model_sampling.ModelSamplingContinuousEDM
    elif model_type == ModelType.V_PREDICTION_CONTINUOUS:
        c = comfy.model_sampling.V_PREDICTION
        s = comfy.model_sampling.ModelSamplingContinuousV
    elif model_type == ModelType.FLUX:
        c = comfy.model_sampling.CONST
        s = comfy.model_sampling.ModelSamplingFlux
    elif model_type == ModelType.IMG_TO_IMG:
        c = comfy.model_sampling.IMG_TO_IMG
    elif model_type == ModelType.FLOW_COSMOS:
        c = comfy.model_sampling.COSMOS_RFLOW
        s = comfy.model_sampling.ModelSamplingCosmosRFlow
    elif model_type == ModelType.IMG_TO_IMG_FLOW:
        c = comfy.model_sampling.IMG_TO_IMG_FLOW

    class ModelSampling(s, c):
        pass

    return ModelSampling(model_config)