def test_metadatarouter_add_self_request():
    # adding a MetadataRequest as `self` adds a copy
    request = MetadataRequest(owner="nested")
    request.fit.add_request(param="param", alias=True)
    router = MetadataRouter(owner="test").add_self_request(request)
    assert str(router._self_request) == str(request)
    # should be a copy, not the same object
    assert router._self_request is not request

    # one can add an estimator as self
    est = ConsumingRegressor().set_fit_request(sample_weight="my_weights")
    router = MetadataRouter(owner="test").add_self_request(obj=est)
    assert str(router._self_request) == str(est.get_metadata_routing())
    assert router._self_request is not est.get_metadata_routing()

    # adding a consumer+router as self should only add the consumer part
    est = WeightedMetaRegressor(
        estimator=ConsumingRegressor().set_fit_request(sample_weight="nested_weights")
    )
    router = MetadataRouter(owner="test").add_self_request(obj=est)
    # _get_metadata_request() returns the consumer part of the requests
    assert str(router._self_request) == str(est._get_metadata_request())
    # get_metadata_routing() returns the complete request set, consumer and
    # router included.
    assert str(router._self_request) != str(est.get_metadata_routing())
    # it should be a copy, not the same object
    assert router._self_request is not est._get_metadata_request()