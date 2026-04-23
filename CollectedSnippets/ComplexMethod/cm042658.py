def test_rel_has_nofollow(self):
        assert rel_has_nofollow("ugc nofollow") is True
        assert rel_has_nofollow("ugc,nofollow") is True
        assert rel_has_nofollow("ugc") is False
        assert rel_has_nofollow("nofollow") is True
        assert rel_has_nofollow("nofollowfoo") is False
        assert rel_has_nofollow("foonofollow") is False
        assert rel_has_nofollow("ugc,  ,  nofollow") is True