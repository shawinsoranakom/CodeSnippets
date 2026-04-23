def test_copy_request(self, pot_request):
        copied_request = pot_request.copy()

        assert copied_request is not pot_request
        assert copied_request.context == pot_request.context
        assert copied_request.innertube_context == pot_request.innertube_context
        assert copied_request.innertube_context is not pot_request.innertube_context
        copied_request.innertube_context['client']['clientName'] = 'ANDROID'
        assert pot_request.innertube_context['client']['clientName'] != 'ANDROID'
        assert copied_request.innertube_host == pot_request.innertube_host
        assert copied_request.session_index == pot_request.session_index
        assert copied_request.player_url == pot_request.player_url
        assert copied_request.is_authenticated == pot_request.is_authenticated
        assert copied_request.visitor_data == pot_request.visitor_data
        assert copied_request.data_sync_id == pot_request.data_sync_id
        assert copied_request.video_id == pot_request.video_id
        assert copied_request.request_cookiejar is pot_request.request_cookiejar
        assert copied_request.request_proxy == pot_request.request_proxy
        assert copied_request.request_headers == pot_request.request_headers
        assert copied_request.request_headers is not pot_request.request_headers
        assert copied_request.request_timeout == pot_request.request_timeout
        assert copied_request.request_source_address == pot_request.request_source_address
        assert copied_request.request_verify_tls == pot_request.request_verify_tls
        assert copied_request.bypass_cache == pot_request.bypass_cache