def test_not_match(script):
    output = 'Uninstalling /usr/local/Cellar/gnuplot/5.0.4_1... (44 files, 2.3M)\n'
    assert not match(Command(script, output))