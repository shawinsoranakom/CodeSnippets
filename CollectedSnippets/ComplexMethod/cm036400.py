def test_multi_connector_worker_metadata(mc):
    class MockConnectorWorkerMetadata(KVConnectorWorkerMetadata):
        def __init__(self, data: set[str]):
            self.data = data

    class MockConnectorWorkerMetadata0(MockConnectorWorkerMetadata):
        def aggregate(
            self, other: KVConnectorWorkerMetadata
        ) -> KVConnectorWorkerMetadata:
            assert isinstance(other, MockConnectorWorkerMetadata)
            return MockConnectorWorkerMetadata0(data=self.data | other.data)

    class MockConnectorWorkerMetadata1(MockConnectorWorkerMetadata):
        def aggregate(
            self, other: KVConnectorWorkerMetadata
        ) -> KVConnectorWorkerMetadata:
            assert isinstance(other, MockConnectorWorkerMetadata)
            return MockConnectorWorkerMetadata1(data=self.data | other.data)

    # -------------------- test build_worker_connector_meta -------------------

    # both connectors return None
    mc._connectors[0].build_connector_worker_meta.return_value = None
    mc._connectors[1].build_connector_worker_meta.return_value = None
    assert mc.build_connector_worker_meta() is None

    # only first connector returns None
    worker_meta1a = MockConnectorWorkerMetadata1({"1a"})
    mc._connectors[0].build_connector_worker_meta.return_value = None
    mc._connectors[1].build_connector_worker_meta.return_value = worker_meta1a
    mc_worker_meta_none_1a = mc.build_connector_worker_meta()
    assert isinstance(mc_worker_meta_none_1a, MultiKVConnectorWorkerMetadata)
    assert mc_worker_meta_none_1a.metadata == (None, worker_meta1a)

    # only second connector returns None
    worker_meta0a = MockConnectorWorkerMetadata0({"0a"})
    mc._connectors[0].build_connector_worker_meta.return_value = worker_meta0a
    mc._connectors[1].build_connector_worker_meta.return_value = None
    mc_worker_meta_0a_none = mc.build_connector_worker_meta()
    assert isinstance(mc_worker_meta_0a_none, MultiKVConnectorWorkerMetadata)
    assert mc_worker_meta_0a_none.metadata == (worker_meta0a, None)

    # both connectors do not return None
    worker_meta0b = MockConnectorWorkerMetadata0({"0b"})
    worker_meta1b = MockConnectorWorkerMetadata1({"1b"})
    mc._connectors[0].build_connector_worker_meta.return_value = worker_meta0b
    mc._connectors[1].build_connector_worker_meta.return_value = worker_meta1b
    mc_worker_meta_0b_1b = mc.build_connector_worker_meta()
    assert isinstance(mc_worker_meta_0b_1b, MultiKVConnectorWorkerMetadata)
    assert mc_worker_meta_0b_1b.metadata == (worker_meta0b, worker_meta1b)

    # ----------------------------- test aggregate ----------------------------

    # aggregate ({"0a"}, None) and (None, {"1a"}) -> ({"0a"}, {"1a"})
    mc_worker_meta_0a_1a = mc_worker_meta_0a_none.aggregate(mc_worker_meta_none_1a)
    assert isinstance(mc_worker_meta_0a_1a, MultiKVConnectorWorkerMetadata)
    assert mc_worker_meta_0a_1a.metadata == (worker_meta0a, worker_meta1a)

    # aggregate ({"0a"}, None) and ({"0b"}, None) -> ({"0a", "0b"}, None)
    mc._connectors[0].build_connector_worker_meta.return_value = worker_meta0b
    mc._connectors[1].build_connector_worker_meta.return_value = None
    mc_worker_meta_0b_none = mc.build_connector_worker_meta()
    mc_worker_meta_0a_0b = mc_worker_meta_0a_none.aggregate(mc_worker_meta_0b_none)
    assert isinstance(mc_worker_meta_0a_0b, MultiKVConnectorWorkerMetadata)
    assert mc_worker_meta_0a_0b.metadata[1] is None
    connector0_md = mc_worker_meta_0a_0b.metadata[0]
    assert isinstance(connector0_md, MockConnectorWorkerMetadata0)
    assert connector0_md.data == {"0a", "0b"}

    # aggregate ({"0a"}, {"1a"}) and ({"0b"}, {"1b"}) -> ({"0a", "0b"}, {"1a", "1b"})
    mc_worker_meta_01a_01b = mc_worker_meta_0a_1a.aggregate(mc_worker_meta_0b_1b)
    assert isinstance(mc_worker_meta_01a_01b, MultiKVConnectorWorkerMetadata)
    metadata = mc_worker_meta_01a_01b.metadata
    assert len(metadata) == 2
    connector0_md, connector1_md = metadata
    assert isinstance(connector0_md, MockConnectorWorkerMetadata0)
    assert isinstance(connector1_md, MockConnectorWorkerMetadata1)
    assert connector0_md.data == {"0a", "0b"}
    assert connector1_md.data == {"1a", "1b"}

    # ---------------------- test update_connector_output ---------------------

    def verify_worker_metadata(expected_metadata: MockConnectorWorkerMetadata | None):
        def _verify_worker_metadata(connector_output: KVConnectorOutput):
            worker_meta = connector_output.kv_connector_worker_meta
            if expected_metadata is None:
                assert worker_meta is None
                return

            assert isinstance(worker_meta, MockConnectorWorkerMetadata)
            assert type(worker_meta) is type(expected_metadata)
            assert expected_metadata.data == worker_meta.data

        return _verify_worker_metadata

    def assert_update_connector_output_called(mc: MultiConnector):
        for c in mc._connectors:
            c.update_connector_output.assert_called_once()
            c.update_connector_output.reset_mock()

    # no worker meta
    kv_connector_output = KVConnectorOutput()
    mc._connectors[0].update_connector_output.side_effect = verify_worker_metadata(None)
    mc._connectors[1].update_connector_output.side_effect = verify_worker_metadata(None)
    mc.update_connector_output(kv_connector_output)
    assert_update_connector_output_called(mc)

    # multi worker meta
    kv_connector_output.kv_connector_worker_meta = mc_worker_meta_01a_01b
    mc._connectors[0].update_connector_output.side_effect = verify_worker_metadata(
        connector0_md
    )
    mc._connectors[1].update_connector_output.side_effect = verify_worker_metadata(
        connector1_md
    )
    mc.update_connector_output(kv_connector_output)
    assert_update_connector_output_called(mc)
    assert kv_connector_output.kv_connector_worker_meta == mc_worker_meta_01a_01b