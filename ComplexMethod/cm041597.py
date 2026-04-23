def test_notes_rest_api(self, infrastructure):
        outputs = infrastructure.get_stack_outputs(self.STACK_NAME)
        gateway_url = outputs["GatewayUrl"]
        base_url = f"{gateway_url}notes"

        response = requests.get(base_url)
        assert response.status_code == 200
        assert json.loads(response.text) == []

        # add some notes
        response = requests.post(base_url, json={"content": "hello world, this is my note"})
        assert response.status_code == 200
        note_1 = json.loads(response.text)

        response = requests.post(base_url, json={"content": "testing is fun :)"})
        assert response.status_code == 200
        note_2 = json.loads(response.text)

        response = requests.post(
            base_url, json={"content": "we will modify and later on remove this note"}
        )
        assert response.status_code == 200
        note_3 = json.loads(response.text)

        # check the notes are returned by the endpoint
        expected = sorted([note_1, note_2, note_3], key=lambda e: e["createdAt"])

        response = requests.get(base_url)
        assert sorted(json.loads(response.text), key=lambda e: e["createdAt"]) == expected

        # retrieve a single note
        response = requests.get(f"{base_url}/{note_1['noteId']}")
        assert response.status_code == 200
        assert json.loads(response.text) == note_1

        # modify a note
        new_content = "this is now new and modified"
        response = requests.put(f"{base_url}/{note_3['noteId']}", json={"content": new_content})
        assert response.status_code == 200

        # retrieve notes
        expected_note_3 = copy.deepcopy(note_3)
        expected_note_3["content"] = new_content

        response = requests.get(base_url)
        assert sorted(json.loads(response.text), key=lambda e: e["createdAt"]) == sorted(
            [note_1, note_2, expected_note_3], key=lambda e: e["createdAt"]
        )

        # delete note
        response = requests.delete(f"{base_url}/{note_2['noteId']}")
        assert response.status_code == 200

        # verify note was deleted
        response = requests.get(base_url)
        assert sorted(json.loads(response.text), key=lambda e: e["createdAt"]) == sorted(
            [note_1, expected_note_3], key=lambda e: e["createdAt"]
        )

        # assert deleted note cannot be retrieved
        response = requests.get(f"{base_url}/{note_2['noteId']}")
        assert response.status_code == 404
        assert json.loads(response.text) == {"status": False, "error": "Item not found."}