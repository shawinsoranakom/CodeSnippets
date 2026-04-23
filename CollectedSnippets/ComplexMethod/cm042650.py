def test_url_is_from_any_domain():
    url = "http://www.wheele-bin-art.co.uk/get/product/123"
    assert url_is_from_any_domain(url, ["wheele-bin-art.co.uk"])
    assert not url_is_from_any_domain(url, ["art.co.uk"])

    url = "http://wheele-bin-art.co.uk/get/product/123"
    assert url_is_from_any_domain(url, ["wheele-bin-art.co.uk"])
    assert not url_is_from_any_domain(url, ["art.co.uk"])

    url = "http://www.Wheele-Bin-Art.co.uk/get/product/123"
    assert url_is_from_any_domain(url, ["wheele-bin-art.CO.UK"])
    assert url_is_from_any_domain(url, ["WHEELE-BIN-ART.CO.UK"])

    url = "http://192.169.0.15:8080/mypage.html"
    assert url_is_from_any_domain(url, ["192.169.0.15:8080"])
    assert not url_is_from_any_domain(url, ["192.169.0.15"])

    url = (
        "javascript:%20document.orderform_2581_1190810811.mode.value=%27add%27;%20"
        "javascript:%20document.orderform_2581_1190810811.submit%28%29"
    )
    assert not url_is_from_any_domain(url, ["testdomain.com"])
    assert not url_is_from_any_domain(url + ".testdomain.com", ["testdomain.com"])