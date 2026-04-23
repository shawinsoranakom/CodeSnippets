def pre_install_dependencies(self):
        if is_aws_cloud() or test_config.TEST_SKIP_LOCALSTACK_START:
            # we don't install the dependencies if LocalStack is not running in process
            return

        if not ffmpeg_installed.is_set() or not vosk_installed.is_set():
            install_async()

        start = int(time.time())
        assert vosk_installed.wait(timeout=INSTALLATION_TIMEOUT), (
            "gave up waiting for Vosk to install"
        )
        elapsed = int(time.time() - start)
        assert ffmpeg_installed.wait(timeout=INSTALLATION_TIMEOUT - elapsed), (
            "gave up waiting for ffmpeg to install"
        )
        LOG.info("Spent %s seconds downloading transcribe dependencies", int(time.time() - start))

        assert not installation_errored.is_set(), "installation of transcribe dependencies failed"