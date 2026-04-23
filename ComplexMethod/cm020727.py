def _mock_dev(
        endpoints,
        ieee="00:0d:6f:00:0a:90:69:e7",
        manufacturer="FakeManufacturer",
        model="FakeModel",
        node_descriptor=b"\x02@\x807\x10\x7fd\x00\x00*d\x00\x00",
        nwk=0xB79C,
        patch_cluster=True,
        quirk=None,
        attributes=None,
    ):
        """Make a fake device using the specified cluster classes."""
        device = zigpy.device.Device(
            zigpy_app_controller, zigpy.types.EUI64.convert(ieee), nwk
        )
        device.manufacturer = manufacturer
        device.model = model
        device.node_desc = zdo_t.NodeDescriptor.deserialize(node_descriptor)[0]
        device.last_seen = time.time()

        for epid, ep in endpoints.items():
            endpoint = device.add_endpoint(epid)
            endpoint.device_type = ep[SIG_EP_TYPE]
            endpoint.profile_id = ep.get(SIG_EP_PROFILE, 0x0104)
            endpoint.request = AsyncMock()

            for cluster_id in ep.get(SIG_EP_INPUT, []):
                endpoint.add_input_cluster(cluster_id)

            for cluster_id in ep.get(SIG_EP_OUTPUT, []):
                endpoint.add_output_cluster(cluster_id)

        device.status = zigpy.device.Status.ENDPOINTS_INIT

        if quirk:
            device = quirk(zigpy_app_controller, device.ieee, device.nwk, device)
        else:
            # Allow zigpy to apply quirks if we don't pass one explicitly
            device = zigpy.quirks.get_device(device)

        if patch_cluster:
            for endpoint in (ep for epid, ep in device.endpoints.items() if epid):
                endpoint.request = AsyncMock(return_value=[0])
                for cluster in itertools.chain(
                    endpoint.in_clusters.values(), endpoint.out_clusters.values()
                ):
                    common_patch_cluster(cluster)

        if attributes is not None:
            for ep_id, clusters in attributes.items():
                for cluster_name, attrs in clusters.items():
                    cluster = getattr(device.endpoints[ep_id], cluster_name)

                    for name, value in attrs.items():
                        attr_id = cluster.find_attribute(name).id
                        cluster._attr_cache[attr_id] = value

        return device