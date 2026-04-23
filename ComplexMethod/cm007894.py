def build_completion(opt_parser):
    opts = [opt for group in opt_parser.option_groups
            for opt in group.option_list]
    opts_file = [opt for opt in opts if opt.metavar == "FILE"]
    opts_dir = [opt for opt in opts if opt.metavar == "DIR"]

    fileopts = []
    for opt in opts_file:
        if opt._short_opts:
            fileopts.extend(opt._short_opts)
        if opt._long_opts:
            fileopts.extend(opt._long_opts)

    diropts = []
    for opt in opts_dir:
        if opt._short_opts:
            diropts.extend(opt._short_opts)
        if opt._long_opts:
            diropts.extend(opt._long_opts)

    flags = [opt.get_opt_string() for opt in opts]

    template = read_file(ZSH_COMPLETION_TEMPLATE)

    template = template.replace("{{fileopts}}", "|".join(fileopts))
    template = template.replace("{{diropts}}", "|".join(diropts))
    template = template.replace("{{flags}}", " ".join(flags))

    write_file(ZSH_COMPLETION_FILE, template)