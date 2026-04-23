def get_options(args: Any) -> Option:
    option: Option = Option()
    if args.__contains__("build"):
        if args.build:
            option.need_build = True

    if args.__contains__("run"):
        if args.run:
            option.need_run = True

    if args.__contains__("merge"):
        if args.merge:
            option.need_merge = True

    if args.__contains__("export"):
        if args.export:
            option.need_export = True

    if args.__contains__("summary"):
        if args.summary:
            option.need_summary = True

    # user does not have specified stage like run
    if not any(vars(option).values()):
        option.need_build = True
        option.need_run = True
        option.need_merge = True
        option.need_export = True
        option.need_summary = True
        option.need_pytest = True

    return option