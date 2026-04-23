def _verify_paginate_results() -> list:
            filtered_state_machines = []
            for page in page_iterator:
                assert 0 < len(page["stateMachines"]) <= 5

                filtered_page = [sm for sm in page["stateMachines"] if sm["name"] in sm_names]
                if filtered_page:
                    sm_name_set = {sm.get("name") for sm in filtered_state_machines}
                    # assert that none of the State Machines being added are already present
                    assert not any(sm.get("name") in sm_name_set for sm in filtered_page)

                    filtered_state_machines.extend(filtered_page)

            assert len(filtered_state_machines) == len(sm_names)
            return filtered_state_machines