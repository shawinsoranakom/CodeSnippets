def test_dns_server_clear(self, dns_server, query_dns):
        """Check if a clear call resets all added entries in the dns server"""
        dns_server.add_host(
            "*.subdomain.example.org", TargetRecord("122.122.122.122", RecordType.A)
        )
        answer = query_dns("sub.subdomain.example.org", "A")
        assert answer.answer
        assert "122.122.122.122" in answer.to_text()

        dns_server.add_skip("skip.subdomain.example.org")
        answer = query_dns("skip.subdomain.example.org", "A")
        assert not answer.answer
        # test if skip does not affect other requests
        answer = query_dns("sub.subdomain.example.org", "A")
        assert answer.answer
        assert "122.122.122.122" in answer.to_text()

        # add alias
        dns_server.add_alias(
            source_name="name.example.org",
            record_type=RecordType.A,
            target=AliasTarget(target="sub.subdomain.example.org"),
        )
        answer = query_dns("name.example.org", "A")
        assert answer.answer
        assert "122.122.122.122" in answer.to_text()

        # clear
        dns_server.clear()
        answer = query_dns("subdomain.example.org", "A")
        assert not answer.answer
        answer = query_dns("skip.example.org", "A")
        assert not answer.answer
        answer = query_dns("name.example.org", "A")
        assert not answer.answer