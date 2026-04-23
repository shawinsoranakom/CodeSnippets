def parse_signature(method) -> Signature:
    isign = inspect.signature(method)

    # strip self and cls from the signature
    param_iter = iter(isign.parameters.values())
    for param in param_iter:
        if param.name in ('self', 'cls'):
            isign = isign.replace(parameters=param_iter)
        break

    # replace BaseModel and such by list[int], see /json/2
    if isign.return_annotation in (
        Self, 'Self',
        models.BaseModel, 'models.BaseModel',
        models.Model, 'models.Model'
    ):
        isign = isign.replace(return_annotation='list[int]')

    # parse the signature
    parameters = {
        param_name: Param.from_inspect(param)
        for param_name, param in isign.parameters.items()
    }
    returns = Return.from_inspect(isign.return_annotation)

    # accumate the decorators such as @api.model
    api = []
    if getattr(method, '_api_model', False):
        api.append('model')
    if getattr(method, '_readonly', False):
        api.append('readonly')

    signature = Signature(parameters, returns, api, raise_={}, doc=None)

    # if the method has a docstring, use it to enhance the signature
    if method.__doc__:
        enhance_signature_using_docstring(signature, method)

    return signature