def run(self):
        if not self.list and not self.download_only and os.geteuid() != 0:
            self.module.fail_json(
                msg="This command has to be run under the root user.",
                failures=[],
                rc=1,
            )

        base = libdnf5.base.Base()
        conf = base.get_config()

        if self.conf_file:
            conf.config_file_path = self.conf_file

        base.load_config()

        if self.releasever is not None:
            variables = base.get_vars()
            variables.set("releasever", self.releasever)
        if self.exclude:
            conf.excludepkgs = self.exclude
        if self.disable_excludes:
            if self.disable_excludes == "all":
                self.disable_excludes = "*"
            conf.disable_excludes = self.disable_excludes
        conf.skip_broken = self.skip_broken
        # best and nobest are mutually exclusive
        if self.nobest is not None:
            conf.best = not self.nobest
        elif self.best is not None:
            conf.best = self.best
        conf.install_weak_deps = self.install_weak_deps
        try:
            # raises AttributeError only on getter if not available
            conf.pkg_gpgcheck   # pylint: disable=pointless-statement
        except AttributeError:
            # dnf5 < 5.2.7.0
            conf.gpgcheck = not self.disable_gpg_check
        else:
            conf.pkg_gpgcheck = not self.disable_gpg_check
        conf.localpkg_gpgcheck = not self.disable_gpg_check
        conf.sslverify = self.sslverify
        conf.clean_requirements_on_remove = self.autoremove

        if not os.path.isdir(self.installroot):
            self.module.fail_json(msg=f"Installroot {self.installroot} must be a directory")

        conf.installroot = self.installroot
        conf.use_host_config = True  # needed for installroot
        conf.cacheonly = "all" if self.cacheonly else "none"
        if self.download_dir:
            conf.destdir = self.download_dir

        if self.enable_plugin:
            try:
                base.enable_disable_plugins(self.enable_plugin, True)
            except AttributeError:
                self.module.fail_json(msg="'enable_plugin' requires python3-libdnf5 5.2.0.0+")

        if self.disable_plugin:
            try:
                base.enable_disable_plugins(self.disable_plugin, False)
            except AttributeError:
                self.module.fail_json(msg="'disable_plugin' requires python3-libdnf5 5.2.0.0+")

        base.setup()

        # https://github.com/rpm-software-management/dnf5/issues/1460
        self.fail_on_non_existing_plugins(base)

        log_router = base.get_logger()
        global_logger = libdnf5.logger.GlobalLogger()
        global_logger.set(log_router.get(), libdnf5.logger.Logger.Level_DEBUG)
        # FIXME hardcoding the filename does not seem right, should libdnf5 expose the default file name?
        logger = libdnf5.logger.create_file_logger(base, "dnf5.log")
        log_router.add_logger(logger)

        if self.update_cache:
            repo_query = libdnf5.repo.RepoQuery(base)
            repo_query.filter_type(libdnf5.repo.Repo.Type_AVAILABLE)
            for repo in repo_query:
                repo_dir = repo.get_cachedir()
                if os.path.exists(repo_dir):
                    repo_cache = libdnf5.repo.RepoCache(base, repo_dir)
                    repo_cache.write_attribute(libdnf5.repo.RepoCache.ATTRIBUTE_EXPIRED)

        sack = base.get_repo_sack()
        sack.create_repos_from_system_configuration()

        repo_query = libdnf5.repo.RepoQuery(base)
        if self.disablerepo:
            repo_query.filter_id(self.disablerepo, libdnf5.common.QueryCmp_IGLOB)
            for repo in repo_query:
                repo.disable()
        if self.enablerepo:
            repo_query.filter_id(self.enablerepo, libdnf5.common.QueryCmp_IGLOB)
            for repo in repo_query:
                repo.enable()

        try:
            sack.load_repos()
        except AttributeError:
            # dnf5 < 5.2.0.0
            sack.update_and_load_enabled_repos(True)

        if self.update_cache and not self.names and not self.list:
            self.module.exit_json(
                msg="Cache updated",
                changed=False,
                results=[],
                rc=0
            )

        if self.list:
            command = self.list
            if command == "updates":
                command = "upgrades"

            if command in {"installed", "upgrades", "available"}:
                query = libdnf5.rpm.PackageQuery(base)
                getattr(query, "filter_{}".format(command))()
                results = [package_to_dict(package) for package in query]
            elif command in {"repos", "repositories"}:
                query = libdnf5.repo.RepoQuery(base)
                query.filter_enabled(True)
                results = [{"repoid": repo.get_id(), "state": "enabled"} for repo in query]
            else:
                resolve_spec_settings = libdnf5.base.ResolveSpecSettings()
                query = libdnf5.rpm.PackageQuery(base)
                query.resolve_pkg_spec(command, resolve_spec_settings, True)
                results = [package_to_dict(package) for package in query]

            self.module.exit_json(msg="", results=results, rc=0)

        settings = libdnf5.base.GoalJobSettings()
        try:
            settings.set_group_with_name(True)
            settings.set_with_binaries(False)
        except AttributeError:
            # dnf5 < 5.2.0.0
            settings.group_with_name = True
            settings.with_binaries = False

        if self.bugfix or self.security:
            advisory_query = libdnf5.advisory.AdvisoryQuery(base)
            types = []
            if self.bugfix:
                types.append("bugfix")
            if self.security:
                types.append("security")
            advisory_query.filter_type(types)
            conf.skip_unavailable = True  # ignore packages that are of a different type, for backwards compat
            settings.set_advisory_filter(advisory_query)

        goal = libdnf5.base.Goal(base)
        results = []
        if self.names == ["*"] and self.state == "latest":
            goal.add_rpm_upgrade(settings)
        elif self.state in {"installed", "present", "latest"}:
            upgrade = self.state == "latest"
            # FIXME use `is_glob_pattern` function when available:
            # https://github.com/rpm-software-management/dnf5/issues/1563
            glob_patterns = set("*[?")
            for spec in self.names:
                if any(set(char) & glob_patterns for char in spec):
                    # Special case for package specs that contain glob characters.
                    # For these we skip `is_installed` and `is_newer_version_installed` tests that allow for the
                    # allow_downgrade feature and pass the package specs to dnf.
                    # Since allow_downgrade is not available in dnf and while it is relatively easy to implement it for
                    # package specs that evaluate to a single package, trying to mimic what would the dnf machinery do
                    # for glob package specs and then filtering those for allow_downgrade appears to always
                    # result in naive/inferior solution.
                    # TODO research how feasible it is to implement the above
                    if upgrade:
                        # for upgrade we pass the spec to both upgrade and install, to satisfy both available and installed
                        # packages evaluated from the glob spec
                        goal.add_upgrade(spec, settings)
                    if not self.update_only:
                        goal.add_install(spec, settings)
                elif is_newer_version_installed(base, spec):
                    if self.allow_downgrade:
                        goal.add_install(spec, settings)
                elif is_installed(base, spec):
                    if upgrade:
                        goal.add_upgrade(spec, settings)
                else:
                    if self.update_only:
                        results.append("Packages providing {} not installed due to update_only specified".format(spec))
                    else:
                        goal.add_install(spec, settings)
        elif self.state in {"absent", "removed"}:
            for spec in self.names:
                goal.add_remove(spec, settings)
            if self.autoremove:
                for pkg in get_unneeded_pkgs(base):
                    goal.add_rpm_remove(pkg, settings)

        goal.set_allow_erasing(self.allowerasing)
        transaction = goal.resolve()

        if transaction.get_problems():
            failures = []
            for log_event in transaction.get_resolve_logs():
                if log_event.get_problem() == libdnf5.base.GoalProblem_NOT_FOUND and self.state in {"installed", "present", "latest"}:
                    # NOTE dnf module compat
                    failures.append("No package {} available.".format(log_event.get_spec()))
                else:
                    failures.append(log_event.to_string())

            if transaction.get_problems() & libdnf5.base.GoalProblem_SOLVER_ERROR != 0:
                msg = "Depsolve Error occurred"
            else:
                msg = "Failed to install some of the specified packages"
            self.module.fail_json(
                msg=msg,
                failures=failures,
                rc=1,
            )

        # NOTE dnf module compat
        actions_compat_map = {
            "Install": "Installed",
            "Remove": "Removed",
            "Replace": "Installed",
            "Upgrade": "Installed",
            "Replaced": "Removed",
        }
        changed = bool(transaction.get_transaction_packages())
        for pkg in transaction.get_transaction_packages():
            if self.download_only:
                action = "Downloaded"
            else:
                action = libdnf5.base.transaction.transaction_item_action_to_string(pkg.get_action())
            results.append("{}: {}".format(actions_compat_map.get(action, action), pkg.get_package().get_nevra()))

        msg = ""
        if self.module.check_mode:
            if results:
                msg = "Check mode: No changes made, but would have if not in check mode"
        elif changed:
            transaction.download()
            if not self.download_only:
                transaction.set_description("ansible dnf5 module")
                result = transaction.run()
                if result == libdnf5.base.Transaction.TransactionRunResult_ERROR_GPG_CHECK:
                    self.module.fail_json(
                        msg="Failed to validate GPG signatures: {}".format(",".join(transaction.get_gpg_signature_problems())),
                        failures=[],
                        rc=1,
                    )
                elif result != libdnf5.base.Transaction.TransactionRunResult_SUCCESS:
                    failures = []
                    if result == libdnf5.base.Transaction.TransactionRunResult_ERROR_RPM_RUN:
                        try:
                            failures = list(transaction.get_rpm_messages())
                        except AttributeError:
                            # get_rpm_messages is not available in dnf5 < 5.2.7.0
                            pass
                    # Add the transaction problems to the failures
                    failures.extend(["{}: {}".format(transaction.transaction_result_to_string(result), log) for log in transaction.get_transaction_problems()])

                    self.module.fail_json(
                        msg="Failed to install some of the specified packages",
                        failures=failures,
                        rc=1,
                    )

        if not msg and not results:
            msg = "Nothing to do"

        self.module.exit_json(
            results=results,
            changed=changed,
            msg=msg,
            rc=0,
        )