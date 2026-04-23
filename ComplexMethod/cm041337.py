def test_store_namespacing(self, sample_stores):
        account1 = "696969696969"
        account2 = "424242424242"

        eu_region = "eu-central-1"
        ap_region = "ap-south-1"

        #
        # For Account 1
        #
        # Get backends for same account but different regions
        backend1_eu = sample_stores[account1][eu_region]
        assert backend1_eu._account_id == account1
        assert backend1_eu._region_name == eu_region
        assert backend1_eu._service_name == "zzz"

        backend1_ap = sample_stores[account1][ap_region]
        assert backend1_ap._account_id == account1
        assert backend1_ap._region_name == ap_region
        assert backend1_ap._service_name == "zzz"

        # Ensure region-specific data isolation
        backend1_eu.region_specific_attr.extend([1, 2, 3])
        assert backend1_ap.region_specific_attr == []

        # Ensure cross-region data sharing
        backend1_eu.CROSS_REGION_ATTR.extend([4, 5, 6])
        assert backend1_ap.CROSS_REGION_ATTR == [4, 5, 6]

        # Ensure global attributes are shared across regions
        assert (
            id(backend1_ap._global)
            == id(backend1_eu._global)
            == id(sample_stores[account1]._global)
        )

        #
        # For Account 2
        #
        # Get backends for a different AWS account
        backend2_eu = sample_stores[account2][eu_region]
        assert backend2_eu._account_id == account2
        assert backend2_eu._region_name == eu_region

        backend2_ap = sample_stores[account2][ap_region]
        assert backend2_ap._account_id == account2
        assert backend2_ap._region_name == ap_region

        # Ensure account-specific data isolation
        assert backend2_eu.CROSS_REGION_ATTR == []
        assert backend2_ap.CROSS_REGION_ATTR == []

        assert backend2_eu.region_specific_attr == []
        assert backend2_ap.region_specific_attr == []

        # Ensure global attributes are shared for same account ID across regions
        assert (
            id(backend2_ap._global)
            == id(backend2_eu._global)
            == id(sample_stores[account2]._global)
            != id(backend1_ap._global)
        )

        # Ensure cross-account data sharing
        backend1_eu.CROSS_ACCOUNT_ATTR.extend([100j, 200j, 300j])
        assert backend1_ap.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j]
        assert backend1_eu.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j]
        assert backend2_ap.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j]
        assert backend2_eu.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j]
        assert (
            id(backend1_ap._universal)
            == id(backend1_eu._universal)
            == id(backend2_ap._universal)
            == id(backend2_eu._universal)
        )