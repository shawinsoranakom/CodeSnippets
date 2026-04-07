def test_common_mixed_case_foreign_keys(self):
        """
        Valid query should be generated when fields fetched from joined tables
        include FKs whose names only differ by case.
        """
        c1 = SimpleCategory.objects.create(name="c1")
        c2 = SimpleCategory.objects.create(name="c2")
        c3 = SimpleCategory.objects.create(name="c3")
        category = CategoryItem.objects.create(category=c1)
        mixed_case_field_category = MixedCaseFieldCategoryItem.objects.create(
            CaTeGoRy=c2
        )
        mixed_case_db_column_category = MixedCaseDbColumnCategoryItem.objects.create(
            category=c3
        )
        CommonMixedCaseForeignKeys.objects.create(
            category=category,
            mixed_case_field_category=mixed_case_field_category,
            mixed_case_db_column_category=mixed_case_db_column_category,
        )
        qs = CommonMixedCaseForeignKeys.objects.values(
            "category",
            "mixed_case_field_category",
            "mixed_case_db_column_category",
            "category__category",
            "mixed_case_field_category__CaTeGoRy",
            "mixed_case_db_column_category__category",
        )
        self.assertTrue(qs.first())