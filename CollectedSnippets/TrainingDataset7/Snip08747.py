def handle(self, *app_labels, **options):
        include_deployment_checks = options["deploy"]
        if options["list_tags"]:
            self.stdout.write(
                "\n".join(sorted(registry.tags_available(include_deployment_checks)))
            )
            return

        if app_labels:
            app_configs = [apps.get_app_config(app_label) for app_label in app_labels]
        else:
            app_configs = None

        tags = options["tags"]
        if tags:
            try:
                invalid_tag = next(
                    tag
                    for tag in tags
                    if not checks.tag_exists(tag, include_deployment_checks)
                )
            except StopIteration:
                # no invalid tags
                pass
            else:
                raise CommandError(
                    'There is no system check with the "%s" tag.' % invalid_tag
                )

        self.check(
            app_configs=app_configs,
            tags=tags,
            display_num_errors=True,
            include_deployment_checks=include_deployment_checks,
            fail_level=getattr(checks, options["fail_level"]),
            databases=options["databases"],
        )