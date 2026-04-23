def test_parsing_with_defaults(self):
        test_env_string = "-e TEST_ENV_VAR=test_string=123"
        test_mount_string = "-v /var/test:/opt/test"
        test_network_string = "--network bridge"
        test_platform_string = "--platform linux/arm64"
        test_privileged_string = "--privileged"
        test_port_string = "-p 80:8080/udp"
        test_port_string_with_host = "-p 127.0.0.1:6000:7000/tcp"
        test_port_string_many_to_one = "-p 9230-9231:9230"
        test_ulimit_string = "--ulimit nofile=768:1024 --ulimit nproc=3"
        test_user_string = "-u sbx_user1051"
        test_dns_string = "--dns 1.2.3.4 --dns 5.6.7.8"
        argument_string = " ".join(
            [
                test_env_string,
                test_mount_string,
                test_network_string,
                test_port_string,
                test_port_string_with_host,
                test_port_string_many_to_one,
                test_platform_string,
                test_privileged_string,
                test_ulimit_string,
                test_user_string,
                test_dns_string,
            ]
        )
        env_vars = {}
        mounts = []
        network = "host"
        platform = DockerPlatform.linux_amd64
        privileged = False
        ports = PortMappings()
        user = "root"
        ulimits = [Ulimit(name="nproc", soft_limit=10, hard_limit=10)]
        flags = Util.parse_additional_flags(
            argument_string,
            env_vars=env_vars,
            volumes=mounts,
            network=network,
            platform=platform,
            privileged=privileged,
            ports=ports,
            ulimits=ulimits,
            user=user,
        )
        assert env_vars == {"TEST_ENV_VAR": "test_string=123"}
        assert mounts == [("/var/test", "/opt/test")]
        assert flags.network == "bridge"
        assert flags.platform == "linux/arm64"
        assert flags.privileged
        assert ports.to_str() == "-p 80:8080/udp -p 6000:7000 -p 9230-9231:9230"
        assert flags.ulimits == [
            Ulimit(name="nproc", soft_limit=3, hard_limit=3),
            Ulimit(name="nofile", soft_limit=768, hard_limit=1024),
        ]
        assert flags.user == "sbx_user1051"
        assert flags.dns == ["1.2.3.4", "5.6.7.8"]

        argument_string = (
            "--add-host host.docker.internal:host-gateway --add-host arbitrary.host:127.0.0.1"
        )
        flags = Util.parse_additional_flags(
            argument_string, env_vars=env_vars, ports=ports, volumes=mounts
        )
        assert {
            "host.docker.internal": "host-gateway",
            "arbitrary.host": "127.0.0.1",
        } == flags.extra_hosts