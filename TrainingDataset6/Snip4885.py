def test_read_users2():  # Just for coverage
    assert asyncio.run(read_users2()) == ["Bean", "Elfo"]