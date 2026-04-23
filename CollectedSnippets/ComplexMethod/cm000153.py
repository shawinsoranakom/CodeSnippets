def test_miller_rabin() -> None:
    """Testing a nontrivial (ends in 1, 3, 7, 9) composite
    and a prime in each range.
    """
    assert not miller_rabin(561)
    assert miller_rabin(563)
    # 2047

    assert not miller_rabin(838_201)
    assert miller_rabin(838_207)
    # 1_373_653

    assert not miller_rabin(17_316_001)
    assert miller_rabin(17_316_017)
    # 25_326_001

    assert not miller_rabin(3_078_386_641)
    assert miller_rabin(3_078_386_653)
    # 3_215_031_751

    assert not miller_rabin(1_713_045_574_801)
    assert miller_rabin(1_713_045_574_819)
    # 2_152_302_898_747

    assert not miller_rabin(2_779_799_728_307)
    assert miller_rabin(2_779_799_728_327)
    # 3_474_749_660_383

    assert not miller_rabin(113_850_023_909_441)
    assert miller_rabin(113_850_023_909_527)
    # 341_550_071_728_321

    assert not miller_rabin(1_275_041_018_848_804_351)
    assert miller_rabin(1_275_041_018_848_804_391)
    # 3_825_123_056_546_413_051

    assert not miller_rabin(79_666_464_458_507_787_791_867)
    assert miller_rabin(79_666_464_458_507_787_791_951)
    # 318_665_857_834_031_151_167_461

    assert not miller_rabin(552_840_677_446_647_897_660_333)
    assert miller_rabin(552_840_677_446_647_897_660_359)