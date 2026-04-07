def test_m2m_inheritance_symmetry(self):
        # Test to ensure that the relationship between two inherited models
        # with a self-referential m2m field maintains symmetry

        sr_child = SelfReferChild(name="Hanna")
        sr_child.save()

        sr_sibling = SelfReferChildSibling(name="Beth")
        sr_sibling.save()
        sr_child.related.add(sr_sibling)

        self.assertSequenceEqual(sr_child.related.all(), [sr_sibling.selfrefer_ptr])
        self.assertSequenceEqual(sr_sibling.related.all(), [sr_child.selfrefer_ptr])