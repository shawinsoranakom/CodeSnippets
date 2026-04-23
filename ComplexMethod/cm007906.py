def test_traversal_re(self):
        mobj = re.fullmatch(r'0(12)(?P<group>3)(4)?', '0123')
        assert traverse_obj(mobj, ...) == [x for x in mobj.groups() if x is not None], \
            '`...` on a `re.Match` should give its `groups()`'
        assert traverse_obj(mobj, lambda k, _: k in (0, 2)) == ['0123', '3'], \
            'function on a `re.Match` should give groupno, value starting at 0'
        assert traverse_obj(mobj, 'group') == '3', \
            'str key on a `re.Match` should give group with that name'
        assert traverse_obj(mobj, 2) == '3', \
            'int key on a `re.Match` should give group with that name'
        assert traverse_obj(mobj, 'gRoUp', casesense=False) == '3', \
            'str key on a `re.Match` should respect casesense'
        assert traverse_obj(mobj, 'fail') is None, \
            'failing str key on a `re.Match` should return `default`'
        assert traverse_obj(mobj, 'gRoUpS', casesense=False) is None, \
            'failing str key on a `re.Match` should return `default`'
        assert traverse_obj(mobj, 8) is None, \
            'failing int key on a `re.Match` should return `default`'
        assert traverse_obj(mobj, lambda k, _: k in (0, 'group')) == ['0123', '3'], \
            'function on a `re.Match` should give group name as well'