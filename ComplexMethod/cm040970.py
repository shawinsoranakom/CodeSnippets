def _install(self, target: InstallTarget):
        # locally import to avoid having a dependency on ASF when starting the CLI
        from localstack.aws.api.opensearch import EngineType
        from localstack.services.opensearch import versions

        version = self.get_elasticsearch_install_version()
        install_dir = self._get_install_dir(target)
        installed_executable = os.path.join(install_dir, "bin", "elasticsearch")
        if not os.path.exists(installed_executable):
            es_url = versions.get_download_url(version, EngineType.Elasticsearch)
            install_dir_parent = os.path.dirname(install_dir)
            mkdir(install_dir_parent)
            # download and extract archive
            tmp_archive = os.path.join(config.dirs.cache, f"localstack.{os.path.basename(es_url)}")
            download_and_extract_with_retry(es_url, tmp_archive, install_dir_parent)
            elasticsearch_dir = glob.glob(os.path.join(install_dir_parent, "elasticsearch*"))
            if not elasticsearch_dir:
                raise Exception(f"Unable to find Elasticsearch folder in {install_dir_parent}")
            shutil.move(elasticsearch_dir[0], install_dir)

            for dir_name in ("data", "logs", "modules", "plugins", "config/scripts"):
                dir_path = os.path.join(install_dir, dir_name)
                mkdir(dir_path)
                chmod_r(dir_path, 0o777)

            # Determine network configuration to use for plugin downloads
            sys_props = {
                **java_system_properties_proxy(),
                **java_system_properties_ssl(
                    os.path.join(install_dir, "jdk", "bin", "keytool"),
                    self.get_java_env_vars(),
                ),
            }
            java_opts = system_properties_to_cli_args(sys_props)

            # install default plugins
            for plugin in ELASTICSEARCH_PLUGIN_LIST:
                plugin_binary = os.path.join(install_dir, "bin", "elasticsearch-plugin")
                plugin_dir = os.path.join(install_dir, "plugins", plugin)
                if not os.path.exists(plugin_dir):
                    LOG.info("Installing Elasticsearch plugin %s", plugin)

                    def try_install():
                        output = run(
                            [plugin_binary, "install", "-b", plugin],
                            env_vars={"ES_JAVA_OPTS": " ".join(java_opts)},
                        )
                        LOG.debug("Plugin installation output: %s", output)

                    # We're occasionally seeing javax.net.ssl.SSLHandshakeException -> add download retries
                    download_attempts = 3
                    try:
                        retry(try_install, retries=download_attempts - 1, sleep=2)
                    except Exception:
                        LOG.warning(
                            "Unable to download Elasticsearch plugin '%s' after %s attempts",
                            plugin,
                            download_attempts,
                        )
                        if not os.environ.get("IGNORE_ES_DOWNLOAD_ERRORS"):
                            raise

            keystore_binary = os.path.join(install_dir, "bin", "elasticsearch-keystore")
            if os.path.exists(keystore_binary):
                # initialize and create the keystore. Concurrent starts of ES will all try to create it at the same
                # time, and fail with a race condition. Creating once when installing solves the issue without
                # the need to lock the starts
                # Ultimately, each cluster should have its own `config` file and maybe not share the same one
                output = run(
                    [keystore_binary, "create"],
                    env_vars={"ES_JAVA_OPTS": " ".join(java_opts)},
                )
                LOG.debug("Keystore init output: %s", output)

        # delete some plugins to free up space
        for plugin in ELASTICSEARCH_DELETE_MODULES:
            module_dir = os.path.join(install_dir, "modules", plugin)
            rm_rf(module_dir)

        # disable x-pack-ml plugin (not working on Alpine)
        xpack_dir = os.path.join(install_dir, "modules", "x-pack-ml", "platform")
        rm_rf(xpack_dir)

        # patch JVM options file - replace hardcoded heap size settings
        jvm_options_file = os.path.join(install_dir, "config", "jvm.options")
        if os.path.exists(jvm_options_file):
            jvm_options = load_file(jvm_options_file)
            jvm_options_replaced = re.sub(
                r"(^-Xm[sx][a-zA-Z0-9.]+$)", r"# \1", jvm_options, flags=re.MULTILINE
            )
            if jvm_options != jvm_options_replaced:
                save_file(jvm_options_file, jvm_options_replaced)