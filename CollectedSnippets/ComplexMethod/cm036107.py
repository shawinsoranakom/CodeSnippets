def assert_equal(obj1: MyType, obj2: MyType):
    assert torch.equal(obj1.tensor1, obj2.tensor1)
    assert obj1.a_string == obj2.a_string
    assert all(
        torch.equal(a, b) for a, b in zip(obj1.list_of_tensors, obj2.list_of_tensors)
    )
    assert np.array_equal(obj1.numpy_array, obj2.numpy_array)
    assert obj1.unrecognized.an_int == obj2.unrecognized.an_int
    assert torch.equal(obj1.small_f_contig_tensor, obj2.small_f_contig_tensor)
    assert torch.equal(obj1.large_f_contig_tensor, obj2.large_f_contig_tensor)
    assert torch.equal(obj1.small_non_contig_tensor, obj2.small_non_contig_tensor)
    assert torch.equal(obj1.large_non_contig_tensor, obj2.large_non_contig_tensor)
    assert torch.equal(obj1.empty_tensor, obj2.empty_tensor)