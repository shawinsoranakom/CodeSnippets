def test_hello(self):
        A = torch.rand(3, 4)
        B = torch.rand(4, 5)
        i, j, k = dims()

        # r = A[i]*4
        r = (A[i, k] * B[k, j]).sum(k).order(i, j)
        torch.testing.assert_close(r, A @ B)

        self.assertEqual(A.sum(), A[i].sum((0, i)))
        self.assertEqual(A.sum(), A[i].sum((-1, i)))

        torch.testing.assert_close(A.sum(), A[i].sum(0, keepdim=True).sum((0, i)))
        torch.testing.assert_close(A[i].std(i, True), A.std(0, True))

        torch.testing.assert_close(A[i, k].max(i)[0].order(k), A.max(0)[0])
        torch.testing.assert_close(A.sort(1)[0], A[i, k].sort(k)[0].order(i, k))
        # XXX - chunk changes the size of a dimension, has to take a new dimension...
        # assert torch.allclose(A.chunk(2,1)[0], A[i, k].chunk(2, k)[0].order(i, k))
        torch.testing.assert_close(A[i].renorm(1, i, 7).order(i), A.renorm(1, 0, 7))
        torch.testing.assert_close(
            A.expand(5, -1, -1), A[i, k].expand(j).order(j, i, k)
        )

        z = dims()
        C = torch.arange(2)
        torch.testing.assert_close(A[:, 0:2], A[i, k].index(k, C[z]).order(i, z))

        o, l = dims()
        o.size = 2
        r = A[i, k].index(k, (o, l))
        torch.testing.assert_close(r.order(i, o, l), A.view(-1, 2, 2))
        rr = r.index((o, l), k)
        torch.testing.assert_close(A, rr.order(i, k))

        r = i + k - 1
        r2 = torch.arange(3)[:, None] + torch.arange(4)[None, :] - 1
        torch.testing.assert_close(r.order(i, k), r2)

        # test with ...
        torch.testing.assert_close(A.T, A[..., k].order(k))

        # test with dimlist
        a_, b_ = dimlists()
        torch.testing.assert_close(A[i, a_].order(*a_, i), A.T)
        # test with one bound dimlist
        torch.testing.assert_close(A[:, a_].order(*a_), A.T)
        # test with a dimlist that will end up empty
        torch.testing.assert_close(A[i, b_, k].order(i, k, *b_), A)
        # test with too few things
        (A[i] + i)
        torch.testing.assert_close((A[i] + i).order(i), A + torch.arange(3)[:, None])
        # test with too many elements
        try:
            A[1, ..., 1, 1]
            raise NotImplementedError
        except IndexError:
            pass
        c, d = dims()
        c.size = 2
        torch.testing.assert_close(A[i, [c, d]].order(i, c, d), A.view(3, 2, 2))

        torch.testing.assert_close(
            A[c + 1, c + 0].order(c), A[torch.arange(2) + 1, torch.arange(2)]
        )

        C = torch.rand(4, 7)
        c_, x, y, z = dims()

        a, b, c = C.split((3, 3, 1), dim=1)
        s = dims()
        ref = C.split((3, 3, 1), dim=1)
        t = C[s, c_].split((x, y, z), dim=c_)
        for a, b, d in zip(ref, t, (x, y, z)):
            torch.testing.assert_close(a, b.order(s, d))

        D = torch.rand(3, 4, 5)
        torch.testing.assert_close(
            D.transpose(0, 1).flatten(1, 2), D[i, k, j].order((i, j)).order(k)
        )

        r = [id(x) for x in torch.rand_like(A[i, k]).dims]
        if not (id(i) in r and id(k) in r):
            raise AssertionError("Expected i and k to be in dims")
        r = [id(x) for x in torch.nn.functional.dropout(A[i, k]).dims]
        if not (id(i) in r and id(k) in r):
            raise AssertionError("Expected i and k to be in dims")