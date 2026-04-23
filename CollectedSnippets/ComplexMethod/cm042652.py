def test_dupename_warning(self, spider_loader_env):
        settings, spiders_dir = spider_loader_env

        # copy 1 spider module so as to have duplicate spider name
        shutil.copyfile(spiders_dir / "spider3.py", spiders_dir / "spider3dupe.py")

        with warnings.catch_warnings(record=True) as w:
            spider_loader = SpiderLoader.from_settings(settings)

            assert len(w) == 1
            msg = str(w[0].message)
            assert "several spiders with the same name" in msg
            assert "'spider3'" in msg
            assert msg.count("'spider3'") == 2

            assert "'spider1'" not in msg
            assert "'spider2'" not in msg
            assert "'spider4'" not in msg

            spiders = set(spider_loader.list())
            assert spiders == {"spider1", "spider2", "spider3", "spider4"}