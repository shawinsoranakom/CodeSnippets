def get_sampler_and_scheduler(sampler_name, scheduler_name, *, convert_automatic=True):
    default_sampler = samplers[0]
    found_scheduler = sd_schedulers.schedulers_map.get(scheduler_name, sd_schedulers.schedulers[0])

    name = sampler_name or default_sampler.name

    for scheduler in sd_schedulers.schedulers:
        name_options = [scheduler.label, scheduler.name, *(scheduler.aliases or [])]

        for name_option in name_options:
            if name.endswith(" " + name_option):
                found_scheduler = scheduler
                name = name[0:-(len(name_option) + 1)]
                break

    sampler = all_samplers_map.get(name, default_sampler)

    # revert back to Automatic if it's the default scheduler for the selected sampler
    if convert_automatic and sampler.options.get('scheduler', None) == found_scheduler.name:
        found_scheduler = sd_schedulers.schedulers[0]

    return sampler.name, found_scheduler.label