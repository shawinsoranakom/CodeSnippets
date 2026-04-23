async def test_post_validate_code(client: AsyncClient, logged_in_headers):
    # Test case with a valid import and function
    code1 = """
import math

def square(x):
    return x ** 2
"""
    response1 = await client.post("api/v1/validate/code", json={"code": code1}, headers=logged_in_headers)
    assert response1.status_code == 200
    assert response1.json() == {"imports": {"errors": []}, "function": {"errors": []}}

    # Test case with an invalid import and valid function
    code2 = """
import non_existent_module

def square(x):
    return x ** 2
"""
    response2 = await client.post("api/v1/validate/code", json={"code": code2}, headers=logged_in_headers)
    assert response2.status_code == 200
    assert response2.json() == {
        "imports": {"errors": ["No module named 'non_existent_module'"]},
        "function": {"errors": []},
    }

    # Test case with a valid import and invalid function syntax
    code3 = """
import math

def square(x)
    return x ** 2
"""
    response3 = await client.post("api/v1/validate/code", json={"code": code3}, headers=logged_in_headers)
    assert response3.status_code == 200
    assert response3.json() == {
        "imports": {"errors": []},
        "function": {"errors": ["expected ':' (<unknown>, line 4)"]},
    }

    # Test case with invalid JSON payload
    response4 = await client.post("api/v1/validate/code", json={"invalid_key": code1}, headers=logged_in_headers)
    assert response4.status_code == 422

    # Test case with an empty code string
    response5 = await client.post("api/v1/validate/code", json={"code": ""}, headers=logged_in_headers)
    assert response5.status_code == 200
    assert response5.json() == {"imports": {"errors": []}, "function": {"errors": []}}

    # Test case with a syntax error in the code
    code6 = """
import math

def square(x)
    return x ** 2
"""
    response6 = await client.post("api/v1/validate/code", json={"code": code6}, headers=logged_in_headers)
    assert response6.status_code == 200
    assert response6.json() == {
        "imports": {"errors": []},
        "function": {"errors": ["expected ':' (<unknown>, line 4)"]},
    }