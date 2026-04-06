def glob(mocker):
    results = {}
    mocker.patch('thefuck.system.Path.glob',
                 new_callable=lambda: lambda *_: results.pop('value', []))
    return lambda value: results.update({'value': value})