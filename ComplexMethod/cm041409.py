def test_dns_server_add_host_lifecycle(self, dns_server, query_dns):
        """Check dns server host entry lifecycle"""
        # add ipv4 host
        dns_server.add_host("example.org", TargetRecord("122.122.122.122", RecordType.A))
        answer = query_dns("example.org", "A")
        assert answer.answer
        assert "122.122.122.122" in answer.to_text()

        # add ipv6 host
        dns_server.add_host("example.org", TargetRecord("::a1", RecordType.AAAA))
        answer = query_dns("example.org", "AAAA")
        assert answer.answer
        assert "122.122.122.122" not in answer.to_text()
        assert "::a1" in answer.to_text()

        # assert ipv6 is not returned in A request
        answer = query_dns("example.org", "A")
        assert answer.answer
        assert "122.122.122.122" in answer.to_text()
        assert "::a1" not in answer.to_text()

        # delete ipv4 host
        dns_server.delete_host("example.org", TargetRecord("122.122.122.122", RecordType.A))
        answer = query_dns("example.org", "A")
        assert answer.answer
        assert "122.122.122.122" not in answer.to_text()

        # check that ipv6 host is unaffected
        answer = query_dns("example.org", "AAAA")
        assert answer.answer
        assert "122.122.122.122" not in answer.to_text()
        assert "::a1" in answer.to_text()

        # delete ipv6 host
        dns_server.delete_host("example.org", TargetRecord("::a1", RecordType.AAAA))
        answer = query_dns("example.org", "AAAA")
        assert answer.answer
        assert "122.122.122.122" not in answer.to_text()
        assert "::a1" not in answer.to_text()