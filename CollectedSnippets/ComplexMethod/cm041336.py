def test_store_reset(self, sample_stores):
        """Ensure reset functionality of Stores and encapsulation works."""
        account1 = "696969696969"
        account2 = "424242424242"

        eu_region = "eu-central-1"
        ap_region = "ap-south-1"

        store1 = sample_stores[account1][eu_region]
        store2 = sample_stores[account1][ap_region]
        store3 = sample_stores[account2][ap_region]

        store1.region_specific_attr.extend([1, 2, 3])
        store1.CROSS_REGION_ATTR.extend(["a", "b", "c"])
        store1.CROSS_ACCOUNT_ATTR.extend([100j, 200j, 300j])
        store2.region_specific_attr.extend([4, 5, 6])
        store2.CROSS_ACCOUNT_ATTR.extend([400j])
        store3.region_specific_attr.extend([7, 8, 9])
        store3.CROSS_REGION_ATTR.extend([0.1, 0.2, 0.3])
        store3.CROSS_ACCOUNT_ATTR.extend([500j])

        # Ensure all stores are affected by cross-account attributes
        assert store1.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j, 500j]
        assert store2.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j, 500j]
        assert store3.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j, 500j]

        assert store1.CROSS_ACCOUNT_ATTR.pop() == 500j

        assert store2.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j]
        assert store3.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j]

        # Ensure other account stores are not affected by RegionBundle reset
        # Ensure cross-account attributes are not affected by RegionBundle reset
        sample_stores[account1].reset()

        assert store1.region_specific_attr == []
        assert store1.CROSS_REGION_ATTR == []
        assert store1.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j]
        assert store2.region_specific_attr == []
        assert store2.CROSS_REGION_ATTR == []
        assert store2.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j]
        assert store3.region_specific_attr == [7, 8, 9]
        assert store3.CROSS_REGION_ATTR == [0.1, 0.2, 0.3]
        assert store3.CROSS_ACCOUNT_ATTR == [100j, 200j, 300j, 400j]

        # Ensure AccountRegionBundle reset
        sample_stores.reset()

        assert store1.CROSS_ACCOUNT_ATTR == []
        assert store2.CROSS_ACCOUNT_ATTR == []
        assert store3.region_specific_attr == []
        assert store3.CROSS_REGION_ATTR == []
        assert store3.CROSS_ACCOUNT_ATTR == []

        # Ensure essential properties are retained after reset
        assert store1._region_name == eu_region
        assert store2._region_name == ap_region
        assert store3._region_name == ap_region
        assert store1._account_id == account1
        assert store2._account_id == account1
        assert store3._account_id == account2