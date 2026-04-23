def test_partial_execution_with_lazy_nodes(self, client: ComfyClient, builder: GraphBuilder):
        g = builder
        input1 = g.node("StubImage", content="BLACK", height=512, width=512, batch_size=1)
        input2 = g.node("StubImage", content="WHITE", height=512, width=512, batch_size=1)
        input3 = g.node("StubImage", content="NOISE", height=512, width=512, batch_size=1)

        # Create masks that will trigger different lazy execution paths
        mask1 = g.node("StubMask", value=0.0, height=512, width=512, batch_size=1)  # Will only need image1
        mask2 = g.node("StubMask", value=0.5, height=512, width=512, batch_size=1)  # Will need both images

        # Create two lazy mix nodes
        lazy_mix1 = g.node("TestLazyMixImages", image1=input1.out(0), image2=input2.out(0), mask=mask1.out(0))
        lazy_mix2 = g.node("TestLazyMixImages", image1=input2.out(0), image2=input3.out(0), mask=mask2.out(0))

        output1 = g.node("SaveImage", images=lazy_mix1.out(0))
        output2 = g.node("SaveImage", images=lazy_mix2.out(0))

        # Run with partial execution targeting only output1
        result = client.run(g, partial_execution_targets=[output1.id])

        # For output1 path - only input1 should run due to lazy evaluation (mask=0.0)
        assert result.was_executed(input1), "Input1 should have been executed"
        assert not result.did_run(input2), "Input2 should not have run (lazy evaluation)"
        assert result.was_executed(mask1), "Mask1 should have been executed"
        assert result.was_executed(lazy_mix1), "Lazy mix1 should have been executed"
        assert result.was_executed(output1), "Output1 should have been executed"

        # Nothing from output2 path should run
        assert not result.did_run(input3), "Input3 should not have run"
        assert not result.did_run(mask2), "Mask2 should not have run"
        assert not result.did_run(lazy_mix2), "Lazy mix2 should not have run"
        assert not result.did_run(output2), "Output2 should not have run"