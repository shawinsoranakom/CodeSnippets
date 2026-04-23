def test_get_collection_versions_pagination(api_version, token_type, token_ins, responses, monkeypatch):
    api = get_test_galaxy_api('https://galaxy.server.com/api/', api_version, token_ins=token_ins)

    if token_ins:
        mock_token_get = MagicMock()
        mock_token_get.return_value = 'my token'
        monkeypatch.setattr(token_ins, 'get', mock_token_get)

    mock_open = MagicMock()
    mock_open.side_effect = [StringIO(to_text(json.dumps(r))) for r in responses]
    monkeypatch.setattr(galaxy_api, 'open_url', mock_open)

    actual = api.get_collection_versions('namespace', 'collection')
    assert actual == [u'1.0.0', u'1.0.1', u'1.0.2', u'1.0.3', u'1.0.4', u'1.0.5']

    assert mock_open.call_count == 3

    query_1 = 'limit=100'
    query_2 = 'limit=100&offset=100'
    query_3 = 'limit=100&offset=200'

    assert mock_open.mock_calls[0][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?%s' % (api_version, query_1)
    assert mock_open.mock_calls[1][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?%s' % (api_version, query_2)
    assert mock_open.mock_calls[2][1][0] == 'https://galaxy.server.com/api/%s/collections/namespace/collection/' \
                                            'versions/?%s' % (api_version, query_3)

    if token_type:
        assert mock_open.mock_calls[0][2]['headers']['Authorization'] == '%s my token' % token_type
        assert mock_open.mock_calls[1][2]['headers']['Authorization'] == '%s my token' % token_type
        assert mock_open.mock_calls[2][2]['headers']['Authorization'] == '%s my token' % token_type