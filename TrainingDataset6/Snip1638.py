def test_info(self, shell, Popen):
        Popen.return_value.stdout.read.side_effect = [
            b'tcsh 6.20.00 (Astron) 2016-11-24 (unknown-unknown-bsd44) \n']
        assert shell.info() == 'Tcsh 6.20.00'
        assert Popen.call_args[0][0] == ['tcsh', '--version']