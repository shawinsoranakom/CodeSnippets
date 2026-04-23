def test_tag_signs(tag_signs):
    assert tag_signs['base.be']['03'] == -1, tag_signs['base.be']
    assert tag_signs['base.be']['49'] == 1, tag_signs['base.be']
    assert tag_signs['base.be']['54'] == -1, tag_signs['base.be']
    assert tag_signs['base.be']['62'] == 1, tag_signs['base.be']
    assert tag_signs['base.be']['64'] == 1, tag_signs['base.be']
    assert tag_signs['base.be']['81'] == 1, tag_signs['base.be']
    assert tag_signs['base.be']['85'] == -1, tag_signs['base.be']
    assert tag_signs['base.it']['4v'] == -1, tag_signs['base.it']