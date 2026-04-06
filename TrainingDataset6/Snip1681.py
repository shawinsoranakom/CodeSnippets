def test_color(settings):
    settings.no_colors = False
    assert logs.color('red') == 'red'
    settings.no_colors = True
    assert logs.color('red') == ''