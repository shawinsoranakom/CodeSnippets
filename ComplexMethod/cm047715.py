def process(model_):
        if model_ in populated:
            return
        if not has_records(model_):  # if there are no records, there is nothing to populate
            populated[model_] = 0
            return

        # if the model has _inherits, the delegated models need to have been populated before the current one
        for model_name in model_._inherits:
            process(model_.env[model_name])

        with ctx.ignore_fkey_constraints(model_), ctx.ignore_indexes(model_):
            populate_model(model_, populated, model_factors, separator_code)

        # models on the other end of X2many relation should also be populated (ex: to avoid SO with no SOL)
        for field in model_._fields.values():
            if field.store and field.copy:
                match field.type:
                    case 'one2many':
                        comodel = model_.env[field.comodel_name]
                        if comodel != model_:
                            model_factors[comodel] = model_factors[model_]
                            process(comodel)
                    case 'many2many':
                        m2m_model = infer_many2many_model(model_.env, field)
                        model_factors[m2m_model] = model_factors[model_]
                        process(m2m_model)