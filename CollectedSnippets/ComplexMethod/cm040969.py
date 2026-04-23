def _install(self, target: InstallTarget):
        # locally import to avoid having a dependency on ASF when starting the CLI
        from localstack.aws.api.opensearch import EngineType
        from localstack.services.opensearch import versions

        version = self._get_opensearch_install_version()
        install_dir = self._get_install_dir(target)
        with _OPENSEARCH_INSTALL_LOCKS[version]:
            if not os.path.exists(install_dir):
                opensearch_url = versions.get_download_url(version, EngineType.OpenSearch)
                install_dir_parent = os.path.dirname(install_dir)
                mkdir(install_dir_parent)
                # download and extract archive
                tmp_archive = os.path.join(
                    config.dirs.cache, f"localstack.{os.path.basename(opensearch_url)}"
                )
                download_and_extract_with_retry(opensearch_url, tmp_archive, install_dir_parent)
                opensearch_dir = glob.glob(os.path.join(install_dir_parent, "opensearch*"))
                if not opensearch_dir:
                    raise Exception(f"Unable to find OpenSearch folder in {install_dir_parent}")
                shutil.move(opensearch_dir[0], install_dir)

                for dir_name in ("data", "logs", "modules", "plugins", "config/scripts"):
                    dir_path = os.path.join(install_dir, dir_name)
                    mkdir(dir_path)
                    chmod_r(dir_path, 0o777)

                parsed_version = semver.VersionInfo.parse(version)

                # setup security based on the version
                self._setup_security(install_dir, parsed_version)

                # Determine network configuration to use for plugin downloads
                sys_props = {
                    **java_system_properties_proxy(),
                    **java_system_properties_ssl(
                        os.path.join(install_dir, "jdk", "bin", "keytool"),
                        {"JAVA_HOME": os.path.join(install_dir, "jdk")},
                    ),
                }
                java_opts = system_properties_to_cli_args(sys_props)

                keystore_binary = os.path.join(install_dir, "bin", "opensearch-keystore")
                if os.path.exists(keystore_binary):
                    # initialize and create the keystore. Concurrent starts of ES will all try to create it at the same
                    # time, and fail with a race condition. Creating once when installing solves the issue without
                    # the need to lock the starts
                    # Ultimately, each cluster should have its own `config` file and maybe not share the same one
                    output = run(
                        [keystore_binary, "create"],
                        env_vars={"OPENSEARCH_JAVA_OPTS": " ".join(java_opts)},
                    )
                    LOG.debug("Keystore init output: %s", output)

                # install other default plugins for opensearch 1.1+
                # https://forum.opensearch.org/t/ingest-attachment-cannot-be-installed/6494/12
                if parsed_version >= "1.1.0":
                    for plugin in OPENSEARCH_PLUGIN_LIST:
                        plugin_binary = os.path.join(install_dir, "bin", "opensearch-plugin")
                        plugin_dir = os.path.join(install_dir, "plugins", plugin)
                        if not os.path.exists(plugin_dir):
                            LOG.info("Installing OpenSearch plugin %s", plugin)

                            def try_install():
                                output = run(
                                    [plugin_binary, "install", "-b", plugin],
                                    env_vars={"OPENSEARCH_JAVA_OPTS": " ".join(java_opts)},
                                )
                                LOG.debug("Plugin installation output: %s", output)

                            # We're occasionally seeing javax.net.ssl.SSLHandshakeException -> add download retries
                            download_attempts = 3
                            try:
                                retry(try_install, retries=download_attempts - 1, sleep=2)
                            except Exception:
                                LOG.warning(
                                    "Unable to download OpenSearch plugin '%s' after %s attempts",
                                    plugin,
                                    download_attempts,
                                )
                                if not os.environ.get("IGNORE_OS_DOWNLOAD_ERRORS"):
                                    raise