def calculate_start_end_timesteps(model, conds):
    s = model.model_sampling
    for t in range(len(conds)):
        x = conds[t]

        timestep_start = None
        timestep_end = None
        # handle clip hook schedule, if needed
        if 'clip_start_percent' in x:
            timestep_start = s.percent_to_sigma(max(x['clip_start_percent'], x.get('start_percent', 0.0)))
            timestep_end = s.percent_to_sigma(min(x['clip_end_percent'], x.get('end_percent', 1.0)))
        else:
            if 'start_percent' in x:
                timestep_start = s.percent_to_sigma(x['start_percent'])
            if 'end_percent' in x:
                timestep_end = s.percent_to_sigma(x['end_percent'])

        if (timestep_start is not None) or (timestep_end is not None):
            n = x.copy()
            if (timestep_start is not None):
                n['timestep_start'] = timestep_start
            if (timestep_end is not None):
                n['timestep_end'] = timestep_end
            conds[t] = n