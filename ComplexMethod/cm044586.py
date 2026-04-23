def test_ratio_resolve():
    assert ratio_resolve(100, []) == []
    assert ratio_resolve(100, [Edge(size=100), Edge(ratio=1)]) == [100, 1]
    assert ratio_resolve(100, [Edge(ratio=1)]) == [100]
    assert ratio_resolve(100, [Edge(ratio=1), Edge(ratio=1)]) == [50, 50]
    assert ratio_resolve(100, [Edge(size=20), Edge(ratio=1), Edge(ratio=1)]) == [
        20,
        40,
        40,
    ]
    assert ratio_resolve(100, [Edge(size=40), Edge(ratio=2), Edge(ratio=1)]) == [
        40,
        40,
        20,
    ]
    assert ratio_resolve(
        100, [Edge(size=40), Edge(ratio=2), Edge(ratio=1, minimum_size=25)]
    ) == [40, 35, 25]
    assert ratio_resolve(100, [Edge(ratio=1), Edge(ratio=1), Edge(ratio=1)]) == [
        33,
        33,
        34,
    ]
    assert ratio_resolve(
        50, [Edge(size=30), Edge(ratio=1, minimum_size=10), Edge(size=30)]
    ) == [30, 10, 30]
    assert ratio_resolve(110, [Edge(ratio=1), Edge(ratio=1), Edge(ratio=1)]) == [
        36,
        37,
        37,
    ]