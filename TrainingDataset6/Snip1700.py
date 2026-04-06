def test_from_script(self, script, result):
        if result:
            assert Command.from_raw_script(script).script == result
        else:
            with pytest.raises(EmptyCommand):
                Command.from_raw_script(script)