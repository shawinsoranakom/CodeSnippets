def test_partition(self):
        d = np.arange(10)
        assert_raises(TypeError, np.partition, d, 2, kind=1)
        assert_raises(ValueError, np.partition, d, 2, kind="nonsense")
        assert_raises(ValueError, np.argpartition, d, 2, kind="nonsense")
        assert_raises(ValueError, d.partition, 2, axis=0, kind="nonsense")
        assert_raises(ValueError, d.argpartition, 2, axis=0, kind="nonsense")
        for k in ("introselect",):
            d = np.array([])
            assert_array_equal(np.partition(d, 0, kind=k), d)
            assert_array_equal(np.argpartition(d, 0, kind=k), d)
            d = np.ones(1)
            assert_array_equal(np.partition(d, 0, kind=k)[0], d)
            assert_array_equal(
                d[np.argpartition(d, 0, kind=k)], np.partition(d, 0, kind=k)
            )

            # kth not modified
            kth = np.array([30, 15, 5])
            okth = kth.copy()
            np.partition(np.arange(40), kth)
            assert_array_equal(kth, okth)

            for r in ([2, 1], [1, 2], [1, 1]):
                d = np.array(r)
                tgt = np.sort(d)
                assert_array_equal(np.partition(d, 0, kind=k)[0], tgt[0])
                assert_array_equal(np.partition(d, 1, kind=k)[1], tgt[1])
                assert_array_equal(
                    d[np.argpartition(d, 0, kind=k)], np.partition(d, 0, kind=k)
                )
                assert_array_equal(
                    d[np.argpartition(d, 1, kind=k)], np.partition(d, 1, kind=k)
                )
                for i in range(d.size):
                    d[i:].partition(0, kind=k)
                assert_array_equal(d, tgt)

            for r in (
                [3, 2, 1],
                [1, 2, 3],
                [2, 1, 3],
                [2, 3, 1],
                [1, 1, 1],
                [1, 2, 2],
                [2, 2, 1],
                [1, 2, 1],
            ):
                d = np.array(r)
                tgt = np.sort(d)
                assert_array_equal(np.partition(d, 0, kind=k)[0], tgt[0])
                assert_array_equal(np.partition(d, 1, kind=k)[1], tgt[1])
                assert_array_equal(np.partition(d, 2, kind=k)[2], tgt[2])
                assert_array_equal(
                    d[np.argpartition(d, 0, kind=k)], np.partition(d, 0, kind=k)
                )
                assert_array_equal(
                    d[np.argpartition(d, 1, kind=k)], np.partition(d, 1, kind=k)
                )
                assert_array_equal(
                    d[np.argpartition(d, 2, kind=k)], np.partition(d, 2, kind=k)
                )
                for i in range(d.size):
                    d[i:].partition(0, kind=k)
                assert_array_equal(d, tgt)

            d = np.ones(50)
            assert_array_equal(np.partition(d, 0, kind=k), d)
            assert_array_equal(
                d[np.argpartition(d, 0, kind=k)], np.partition(d, 0, kind=k)
            )

            # sorted
            d = np.arange(49)
            assert_equal(np.partition(d, 5, kind=k)[5], 5)
            assert_equal(np.partition(d, 15, kind=k)[15], 15)
            assert_array_equal(
                d[np.argpartition(d, 5, kind=k)], np.partition(d, 5, kind=k)
            )
            assert_array_equal(
                d[np.argpartition(d, 15, kind=k)], np.partition(d, 15, kind=k)
            )

            # rsorted
            d = np.arange(47)[::-1]
            assert_equal(np.partition(d, 6, kind=k)[6], 6)
            assert_equal(np.partition(d, 16, kind=k)[16], 16)
            assert_array_equal(
                d[np.argpartition(d, 6, kind=k)], np.partition(d, 6, kind=k)
            )
            assert_array_equal(
                d[np.argpartition(d, 16, kind=k)], np.partition(d, 16, kind=k)
            )

            assert_array_equal(np.partition(d, -6, kind=k), np.partition(d, 41, kind=k))
            assert_array_equal(
                np.partition(d, -16, kind=k), np.partition(d, 31, kind=k)
            )
            assert_array_equal(
                d[np.argpartition(d, -6, kind=k)], np.partition(d, 41, kind=k)
            )

            # median of 3 killer, O(n^2) on pure median 3 pivot quickselect
            # exercises the median of median of 5 code used to keep O(n)
            d = np.arange(1000000)
            x = np.roll(d, d.size // 2)
            mid = x.size // 2 + 1
            assert_equal(np.partition(x, mid)[mid], mid)
            d = np.arange(1000001)
            x = np.roll(d, d.size // 2 + 1)
            mid = x.size // 2 + 1
            assert_equal(np.partition(x, mid)[mid], mid)

            # max
            d = np.ones(10)
            d[1] = 4
            assert_equal(np.partition(d, (2, -1))[-1], 4)
            assert_equal(np.partition(d, (2, -1))[2], 1)
            assert_equal(d[np.argpartition(d, (2, -1))][-1], 4)
            assert_equal(d[np.argpartition(d, (2, -1))][2], 1)
            d[1] = np.nan
            assert_(np.isnan(d[np.argpartition(d, (2, -1))][-1]))
            assert_(np.isnan(np.partition(d, (2, -1))[-1]))

            # equal elements
            d = np.arange(47) % 7
            tgt = np.sort(np.arange(47) % 7)
            np.random.shuffle(d)
            for i in range(d.size):
                assert_equal(np.partition(d, i, kind=k)[i], tgt[i])
            assert_array_equal(
                d[np.argpartition(d, 6, kind=k)], np.partition(d, 6, kind=k)
            )
            assert_array_equal(
                d[np.argpartition(d, 16, kind=k)], np.partition(d, 16, kind=k)
            )
            for i in range(d.size):
                d[i:].partition(0, kind=k)
            assert_array_equal(d, tgt)

            d = np.array(
                [0, 1, 2, 3, 4, 5, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 9]
            )
            kth = [0, 3, 19, 20]
            assert_equal(np.partition(d, kth, kind=k)[kth], (0, 3, 7, 7))
            assert_equal(d[np.argpartition(d, kth, kind=k)][kth], (0, 3, 7, 7))

            d = np.array([2, 1])
            d.partition(0, kind=k)
            assert_raises(ValueError, d.partition, 2)
            assert_raises(np.AxisError, d.partition, 3, axis=1)
            assert_raises(ValueError, np.partition, d, 2)
            assert_raises(np.AxisError, np.partition, d, 2, axis=1)
            assert_raises(ValueError, d.argpartition, 2)
            assert_raises(np.AxisError, d.argpartition, 3, axis=1)
            assert_raises(ValueError, np.argpartition, d, 2)
            assert_raises(np.AxisError, np.argpartition, d, 2, axis=1)
            d = np.arange(10).reshape((2, 5))
            d.partition(1, axis=0, kind=k)
            d.partition(4, axis=1, kind=k)
            np.partition(d, 1, axis=0, kind=k)
            np.partition(d, 4, axis=1, kind=k)
            np.partition(d, 1, axis=None, kind=k)
            np.partition(d, 9, axis=None, kind=k)
            d.argpartition(1, axis=0, kind=k)
            d.argpartition(4, axis=1, kind=k)
            np.argpartition(d, 1, axis=0, kind=k)
            np.argpartition(d, 4, axis=1, kind=k)
            np.argpartition(d, 1, axis=None, kind=k)
            np.argpartition(d, 9, axis=None, kind=k)
            assert_raises(ValueError, d.partition, 2, axis=0)
            assert_raises(ValueError, d.partition, 11, axis=1)
            assert_raises(TypeError, d.partition, 2, axis=None)
            assert_raises(ValueError, np.partition, d, 9, axis=1)
            assert_raises(ValueError, np.partition, d, 11, axis=None)
            assert_raises(ValueError, d.argpartition, 2, axis=0)
            assert_raises(ValueError, d.argpartition, 11, axis=1)
            assert_raises(ValueError, np.argpartition, d, 9, axis=1)
            assert_raises(ValueError, np.argpartition, d, 11, axis=None)

            td = [
                (dt, s) for dt in [np.int32, np.float32, np.complex64] for s in (9, 16)
            ]
            for dt, s in td:
                aae = assert_array_equal
                at = assert_

                d = np.arange(s, dtype=dt)
                np.random.shuffle(d)
                d1 = np.tile(np.arange(s, dtype=dt), (4, 1))
                map(np.random.shuffle, d1)
                d0 = np.transpose(d1)
                for i in range(d.size):
                    p = np.partition(d, i, kind=k)
                    assert_equal(p[i], i)
                    # all before are smaller
                    assert_array_less(p[:i], p[i])
                    # all after are larger
                    assert_array_less(p[i], p[i + 1 :])
                    aae(p, d[np.argpartition(d, i, kind=k)])

                    p = np.partition(d1, i, axis=1, kind=k)
                    aae(p[:, i], np.array([i] * d1.shape[0], dtype=dt))
                    # array_less does not seem to work right
                    at(
                        (p[:, :i].T <= p[:, i]).all(),
                        msg=f"{i:d}: {p[:, i]!r} <= {p[:, :i].T!r}",
                    )
                    at(
                        (p[:, i + 1 :].T > p[:, i]).all(),
                        msg=f"{i:d}: {p[:, i]!r} < {p[:, i + 1 :].T!r}",
                    )
                    aae(
                        p,
                        d1[
                            np.arange(d1.shape[0])[:, None],
                            np.argpartition(d1, i, axis=1, kind=k),
                        ],
                    )

                    p = np.partition(d0, i, axis=0, kind=k)
                    aae(p[i, :], np.array([i] * d1.shape[0], dtype=dt))
                    # array_less does not seem to work right
                    at(
                        (p[:i, :] <= p[i, :]).all(),
                        msg=f"{i:d}: {p[i, :]!r} <= {p[:i, :]!r}",
                    )
                    at(
                        (p[i + 1 :, :] > p[i, :]).all(),
                        msg=f"{i:d}: {p[i, :]!r} < {p[:, i + 1 :]!r}",
                    )
                    aae(
                        p,
                        d0[
                            np.argpartition(d0, i, axis=0, kind=k),
                            np.arange(d0.shape[1])[None, :],
                        ],
                    )

                    # check inplace
                    dc = d.copy()
                    dc.partition(i, kind=k)
                    assert_equal(dc, np.partition(d, i, kind=k))
                    dc = d0.copy()
                    dc.partition(i, axis=0, kind=k)
                    assert_equal(dc, np.partition(d0, i, axis=0, kind=k))
                    dc = d1.copy()
                    dc.partition(i, axis=1, kind=k)
                    assert_equal(dc, np.partition(d1, i, axis=1, kind=k))