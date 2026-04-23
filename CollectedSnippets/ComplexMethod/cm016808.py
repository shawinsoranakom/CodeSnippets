def test_partial_execution_multiple_output_nodes(self, client: ComfyClient, builder: GraphBuilder):
        g = builder
        input1 = g.node("StubImage", content="BLACK", height=512, width=512, batch_size=1)
        input2 = g.node("StubImage", content="WHITE", height=512, width=512, batch_size=1)

        # Create a chain of OUTPUT_NODEs
        output_node1 = g.node("TestOutputNodeWithSocketOutput", image=input1.out(0), value=1.5)
        output_node2 = g.node("TestOutputNodeWithSocketOutput", image=output_node1.out(0), value=2.0)

        # Create regular output nodes
        save1 = g.node("SaveImage", images=output_node1.out(0))
        save2 = g.node("SaveImage", images=output_node2.out(0))
        save3 = g.node("SaveImage", images=input2.out(0))

        # Run targeting only save2
        result = client.run(g, partial_execution_targets=[save2.id])

        # Should run: input1, output_node1, output_node2, save2
        assert result.was_executed(input1), "Input1 should have been executed"
        assert result.was_executed(output_node1), "Output node 1 should have been executed (dependency)"
        assert result.was_executed(output_node2), "Output node 2 should have been executed (dependency)"
        assert result.was_executed(save2), "Save2 should have been executed"

        # Should NOT run: input2, save1, save3
        assert not result.did_run(input2), "Input2 should not have run"
        assert not result.did_run(save1), "Save1 should not have run"
        assert not result.did_run(save3), "Save3 should not have run"