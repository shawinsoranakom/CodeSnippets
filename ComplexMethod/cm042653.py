def test_multiple_dupename_warning(self, spider_loader_env):
        settings, spiders_dir = spider_loader_env
        # copy 2 spider modules so as to have duplicate spider name
        # This should issue 2 warning, 1 for each duplicate spider name
        shutil.copyfile(spiders_dir / "spider1.py", spiders_dir / "spider1dupe.py")
        shutil.copyfile(spiders_dir / "spider2.py", spiders_dir / "spider2dupe.py")

        with warnings.catch_warnings(record=True) as w:
            spider_loader = SpiderLoader.from_settings(settings)

            assert len(w) == 1
            msg = str(w[0].message)
            assert "several spiders with the same name" in msg
            assert "'spider1'" in msg
            assert msg.count("'spider1'") == 2

            assert "'spider2'" in msg
            assert msg.count("'spider2'") == 2

            assert "'spider3'" not in msg
            assert "'spider4'" not in msg

            spiders = set(spider_loader.list())
            assert spiders == {"spider1", "spider2", "spider3", "spider4"}