def check(
        self,
        app_configs=None,
        tags=None,
        display_num_errors=False,
        include_deployment_checks=False,
        fail_level=checks.ERROR,
        databases=None,
    ):
        """
        Use the system check framework to validate entire Django project.
        Raise CommandError for any serious message (error or critical errors).
        If there are only light messages (like warnings), print them to stderr
        and don't raise an exception.
        """
        all_issues = checks.run_checks(
            app_configs=app_configs,
            tags=tags,
            include_deployment_checks=include_deployment_checks,
            databases=databases,
        )

        header, body, footer = "", "", ""
        visible_issue_count = 0  # excludes silenced warnings

        if all_issues:
            debugs = [
                e for e in all_issues if e.level < checks.INFO and not e.is_silenced()
            ]
            infos = [
                e
                for e in all_issues
                if checks.INFO <= e.level < checks.WARNING and not e.is_silenced()
            ]
            warnings = [
                e
                for e in all_issues
                if checks.WARNING <= e.level < checks.ERROR and not e.is_silenced()
            ]
            errors = [
                e
                for e in all_issues
                if checks.ERROR <= e.level < checks.CRITICAL and not e.is_silenced()
            ]
            criticals = [
                e
                for e in all_issues
                if checks.CRITICAL <= e.level and not e.is_silenced()
            ]
            sorted_issues = [
                (criticals, "CRITICALS"),
                (errors, "ERRORS"),
                (warnings, "WARNINGS"),
                (infos, "INFOS"),
                (debugs, "DEBUGS"),
            ]

            for issues, group_name in sorted_issues:
                if issues:
                    visible_issue_count += len(issues)
                    formatted = (
                        (
                            self.style.ERROR(str(e))
                            if e.is_serious()
                            else self.style.WARNING(str(e))
                        )
                        for e in issues
                    )
                    formatted = "\n".join(sorted(formatted))
                    body += "\n%s:\n%s\n" % (group_name, formatted)

        if visible_issue_count:
            header = "System check identified some issues:\n"

        if display_num_errors:
            if visible_issue_count:
                footer += "\n"
            footer += "System check identified %s (%s silenced)." % (
                (
                    "no issues"
                    if visible_issue_count == 0
                    else (
                        "1 issue"
                        if visible_issue_count == 1
                        else "%s issues" % visible_issue_count
                    )
                ),
                len(all_issues) - visible_issue_count,
            )

        if any(e.is_serious(fail_level) and not e.is_silenced() for e in all_issues):
            msg = self.style.ERROR("SystemCheckError: %s" % header) + body + footer
            raise SystemCheckError(msg)
        else:
            msg = header + body + footer

        if msg:
            if visible_issue_count:
                self.stderr.write(msg, lambda x: x)
            else:
                self.stdout.write(msg)