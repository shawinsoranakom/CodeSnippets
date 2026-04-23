def test_distro_known(self):
        with patch('ansible.module_utils.distro.id', return_value="alpine"):
            assert get_distribution() == "Alpine"

        with patch('ansible.module_utils.distro.id', return_value="arch"):
            assert get_distribution() == "Arch"

        with patch('ansible.module_utils.distro.id', return_value="centos"):
            assert get_distribution() == "Centos"

        with patch('ansible.module_utils.distro.id', return_value="clear-linux-os"):
            assert get_distribution() == "Clear-linux-os"

        with patch('ansible.module_utils.distro.id', return_value="coreos"):
            assert get_distribution() == "Coreos"

        with patch('ansible.module_utils.distro.id', return_value="debian"):
            assert get_distribution() == "Debian"

        with patch('ansible.module_utils.distro.id', return_value="flatcar"):
            assert get_distribution() == "Flatcar"

        with patch('ansible.module_utils.distro.id', return_value="linuxmint"):
            assert get_distribution() == "Linuxmint"

        with patch('ansible.module_utils.distro.id', return_value="opensuse"):
            assert get_distribution() == "Opensuse"

        with patch('ansible.module_utils.distro.id', return_value="oracle"):
            assert get_distribution() == "Oracle"

        with patch('ansible.module_utils.distro.id', return_value="raspian"):
            assert get_distribution() == "Raspian"

        with patch('ansible.module_utils.distro.id', return_value="rhel"):
            assert get_distribution() == "Redhat"

        with patch('ansible.module_utils.distro.id', return_value="ubuntu"):
            assert get_distribution() == "Ubuntu"

        with patch('ansible.module_utils.distro.id', return_value="virtuozzo"):
            assert get_distribution() == "Virtuozzo"

        with patch('ansible.module_utils.distro.id', return_value="foo"):
            assert get_distribution() == "Foo"