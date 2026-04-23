def test_nested_arrays_with_object_schemas() -> None:
    """Test deeply nested arrays with object schemas create proper Pydantic models."""
    schema = {
        "type": "object",
        "properties": {
            "companies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "departments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "employees": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "role": {"type": "string"},
                                                "skills": {"type": "array", "items": {"type": "string"}},
                                            },
                                            "required": ["name", "role"],
                                        },
                                    },
                                },
                                "required": ["name"],
                            },
                        },
                    },
                    "required": ["name"],
                },
            }
        },
    }

    converter = _JSONSchemaToPydantic()
    Model = converter.json_schema_to_pydantic(schema, "CompanyListModel")

    # Verify companies field type annotation
    companies_field = Model.model_fields["companies"]
    from typing import Union, get_args, get_origin

    # Extract companies inner type
    actual_list_type = companies_field.annotation
    if get_origin(companies_field.annotation) is Union:
        union_args = get_args(companies_field.annotation)
        for arg in union_args:
            if get_origin(arg) is list:
                actual_list_type = arg
                break

    assert get_origin(actual_list_type) is list
    company_type = get_args(actual_list_type)[0]

    # Verify companies are BaseModel subclasses
    assert company_type is not dict
    assert hasattr(company_type, "model_fields")
    assert "name" in company_type.model_fields
    assert "departments" in company_type.model_fields

    # Verify departments field type annotation
    departments_field = company_type.model_fields["departments"]
    dept_list_type = departments_field.annotation
    if get_origin(dept_list_type) is Union:
        union_args = get_args(dept_list_type)
        for arg in union_args:
            if get_origin(arg) is list:
                dept_list_type = arg
                break

    assert get_origin(dept_list_type) is list
    department_type = get_args(dept_list_type)[0]

    # Verify departments are BaseModel subclasses
    assert department_type is not dict
    assert hasattr(department_type, "model_fields")
    assert "name" in department_type.model_fields
    assert "employees" in department_type.model_fields

    # Verify employees field type annotation
    employees_field = department_type.model_fields["employees"]
    emp_list_type = employees_field.annotation
    if get_origin(emp_list_type) is Union:
        union_args = get_args(emp_list_type)
        for arg in union_args:
            if get_origin(arg) is list:
                emp_list_type = arg
                break

    assert get_origin(emp_list_type) is list
    employee_type = get_args(emp_list_type)[0]

    # Verify employees are BaseModel subclasses
    assert employee_type is not dict
    assert hasattr(employee_type, "model_fields")
    expected_emp_fields = {"name", "role", "skills"}
    actual_emp_fields = set(employee_type.model_fields.keys())
    assert expected_emp_fields.issubset(actual_emp_fields)

    # Test instantiation with nested data
    test_data = {
        "companies": [
            {
                "name": "TechCorp",
                "departments": [
                    {
                        "name": "Engineering",
                        "employees": [
                            {"name": "Alice", "role": "Senior Developer", "skills": ["Python", "JavaScript", "Docker"]},
                            {"name": "Bob", "role": "DevOps Engineer", "skills": ["Kubernetes", "AWS"]},
                        ],
                    },
                    {"name": "Marketing", "employees": [{"name": "Carol", "role": "Marketing Manager"}]},
                ],
            }
        ]
    }

    instance = Model(**test_data)
    assert len(instance.companies) == 1  # type: ignore[attr-defined]

    company = instance.companies[0]  # type: ignore[attr-defined]
    assert hasattr(company, "model_fields")  # type: ignore[reportUnknownArgumentType]
    assert company.name == "TechCorp"  # type: ignore[attr-defined]
    assert len(company.departments) == 2  # type: ignore[attr-defined]

    engineering_dept = company.departments[0]  # type: ignore[attr-defined]
    assert hasattr(engineering_dept, "model_fields")  # type: ignore[reportUnknownArgumentType]
    assert engineering_dept.name == "Engineering"  # type: ignore[attr-defined]
    assert len(engineering_dept.employees) == 2  # type: ignore[attr-defined]

    alice = engineering_dept.employees[0]  # type: ignore[attr-defined]
    assert hasattr(alice, "model_fields")  # type: ignore[reportUnknownArgumentType]
    assert alice.name == "Alice"  # type: ignore[attr-defined]
    assert alice.role == "Senior Developer"  # type: ignore[attr-defined]
    assert alice.skills == ["Python", "JavaScript", "Docker"]