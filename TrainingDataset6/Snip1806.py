def how_to_configure_alias(configuration_details):
    print(u"Seems like {bold}fuck{reset} alias isn't configured!".format(
        bold=color(colorama.Style.BRIGHT),
        reset=color(colorama.Style.RESET_ALL)))

    if configuration_details:
        print(
            u"Please put {bold}{content}{reset} in your "
            u"{bold}{path}{reset} and apply "
            u"changes with {bold}{reload}{reset} or restart your shell.".format(
                bold=color(colorama.Style.BRIGHT),
                reset=color(colorama.Style.RESET_ALL),
                **configuration_details._asdict()))

        if configuration_details.can_configure_automatically:
            print(
                u"Or run {bold}fuck{reset} a second time to configure"
                u" it automatically.".format(
                    bold=color(colorama.Style.BRIGHT),
                    reset=color(colorama.Style.RESET_ALL)))

    print(u'More details - https://github.com/nvbn/thefuck#manual-installation')