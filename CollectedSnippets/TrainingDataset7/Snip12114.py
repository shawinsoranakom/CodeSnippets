def check(opts):
        return (
            model._meta.concrete_model == opts.concrete_model
            or opts.concrete_model in model._meta.all_parents
            or model in opts.all_parents
        )