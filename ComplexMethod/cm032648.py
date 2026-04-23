def test_add_to_multiple_memory(self, WebApiAuth):
        memory_ids = self.memory_ids
        agent_id = uuid.uuid4().hex
        session_id = uuid.uuid4().hex
        message_payload = {
            "memory_id": memory_ids,
            "agent_id": agent_id,
            "session_id": session_id,
            "user_id": "",
            "user_input": "what is pineapple?",
            "agent_response": """
A pineapple is a tropical fruit known for its sweet, tangy flavor and distinctive, spiky appearance. Here are the key facts:
Scientific Name: Ananas comosus
Physical Description: It has a tough, spiky, diamond-patterned outer skin (rind) that is usually green, yellow, or brownish. Inside, the juicy yellow flesh surrounds a fibrous core.
Growth: Unlike most fruits, pineapples do not grow on trees. They grow from a central stem as a composite fruit, meaning they are formed from many individual berries that fuse together around the core. They grow on a short, leafy plant close to the ground.
Uses: Pineapples are eaten fresh, cooked, grilled, juiced, or canned. They are a popular ingredient in desserts, fruit salads, savory dishes (like pizzas or ham glazes), smoothies, and cocktails.
Nutrition: They are a good source of Vitamin C, manganese, and contain an enzyme called bromelain, which aids in digestion and can tenderize meat.
Symbolism: The pineapple is a traditional symbol of hospitality and welcome in many cultures.
Are you asking about the fruit itself, or its use in a specific context?
"""
        }
        add_res = add_message(WebApiAuth, message_payload)
        assert add_res["code"] == 0, add_res
        time.sleep(2)  # make sure refresh to index before search
        for memory_id in memory_ids:
            message_res = list_memory_message(WebApiAuth, memory_id, params={"agent_id": agent_id, "keywords": session_id})
            assert message_res["code"] == 0, message_res
            assert message_res["data"]["messages"]["total_count"] > 0
            for message in message_res["data"]["messages"]["message_list"]:
                assert message["agent_id"] == agent_id, message
                assert message["session_id"] == session_id, message