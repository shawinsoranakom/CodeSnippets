def test_get_domain_names(aws_client):
    # create domain name
    domain_name = f"domain-{short_uid()}"
    test_certificate_name = "test.certificate"
    response = aws_client.apigateway.create_domain_name(
        domainName=domain_name, certificateName=test_certificate_name
    )
    assert response["domainName"] == domain_name
    assert response["certificateName"] == test_certificate_name
    assert response["domainNameStatus"] == "AVAILABLE"

    # get new domain name
    result = aws_client.apigateway.get_domain_names()
    added = [dom for dom in result["items"] if dom["domainName"] == domain_name]
    assert added
    assert added[0]["domainName"] == domain_name
    assert added[0]["certificateName"] == test_certificate_name
    assert added[0]["domainNameStatus"] == "AVAILABLE"