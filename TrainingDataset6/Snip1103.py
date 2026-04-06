def test_match(output):
    assert match(Command('./manage.py migrate', output))
    assert match(Command('python manage.py migrate', output))
    assert not match(Command('./manage.py migrate', ''))
    assert not match(Command('app migrate', output))
    assert not match(Command('./manage.py test', output))