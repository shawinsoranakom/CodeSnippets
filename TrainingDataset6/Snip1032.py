def test_get_new_command(brew_no_available_formula_one, brew_no_available_formula_two,
                         brew_no_available_formula_three):
    assert get_new_command(Command('brew install giss',
                                   brew_no_available_formula_one))\
        == ['brew install gist']
    assert get_new_command(Command('brew install elasticsear',
                                   brew_no_available_formula_two))\
        == ['brew install elasticsearch', 'brew install elasticsearch@6']
    assert get_new_command(Command('brew install gitt',
                                   brew_no_available_formula_three))\
        == ['brew install git', 'brew install gitg', 'brew install gist']

    assert get_new_command(Command('brew install aa',
                                   brew_no_available_formula_one))\
        != 'brew install aha'