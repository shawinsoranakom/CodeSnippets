def test_match():
    script = "git push -u origin master"
    output = "error: src refspec master does not match any\nerror: failed to..."
    assert match(Command(script, output))