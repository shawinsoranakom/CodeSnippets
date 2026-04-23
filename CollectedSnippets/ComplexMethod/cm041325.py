def test_can_parse_apache_bsd_format(self):
        """Test detection of Apache BSD checksum format."""
        parser = ApacheBSDFormat()

        # Valid Apache BSD format
        assert parser.can_parse("file.txt: d41d8cd9 8f00b204\n         e9800998 ecf8427e")
        assert parser.can_parse("test.zip: e3b0c442 98fc1c14")
        assert parser.can_parse("file: abcd1234")

        # Invalid formats
        assert not parser.can_parse("d41d8cd98f00b204e9800998ecf8427e  file.txt")
        assert not parser.can_parse("MD5 (file.txt) = d41d8cd98f00b204e9800998ecf8427e")
        assert not parser.can_parse("no colon here")
        assert not parser.can_parse("")