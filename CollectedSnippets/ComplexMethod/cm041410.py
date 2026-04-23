def test_dns_server_add_host_lifecycle_with_ids(self, dns_server, query_dns):
        """Check if deletion with and without ids works as expected"""
        # add ipv4 hosts
        dns_server.add_host("example.org", TargetRecord("1.1.1.1", RecordType.A, record_id="1"))
        dns_server.add_host("example.org", TargetRecord("2.2.2.2", RecordType.A, record_id="2"))
        dns_server.add_host("example.org", TargetRecord("3.3.3.3", RecordType.A))
        dns_server.add_host("example.org", TargetRecord("4.4.4.4", RecordType.A))

        # check if all are returned
        answer = query_dns("example.org", "A")
        assert answer.answer
        assert "1.1.1.1" in answer.to_text()
        assert "2.2.2.2" in answer.to_text()
        assert "3.3.3.3" in answer.to_text()
        assert "4.4.4.4" in answer.to_text()

        # delete by id, check if others are still present
        dns_server.delete_host("example.org", TargetRecord("", RecordType.A, record_id="1"))
        answer = query_dns("example.org", "A")
        assert answer.answer
        assert "2.2.2.2" in answer.to_text()
        assert "3.3.3.3" in answer.to_text()
        assert "4.4.4.4" in answer.to_text()
        assert "1.1.1.1" not in answer.to_text()

        # delete without id, check if others are still present
        dns_server.delete_host("example.org", TargetRecord("", RecordType.A))
        answer = query_dns("example.org", "A")
        assert answer.answer
        assert "2.2.2.2" in answer.to_text()
        assert "3.3.3.3" not in answer.to_text()
        assert "4.4.4.4" not in answer.to_text()
        assert "1.1.1.1" not in answer.to_text()