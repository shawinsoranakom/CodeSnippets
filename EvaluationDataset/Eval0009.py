class ExampleClass:
    def __init__(self, name):
        self.name = name
    def process_data(self, data):
        return f"Processed {data} with {self.name}"

    @traced(span_name="custom_operation")
    def special_operation(self, value):
        return value * 2

    @traced(
        additional_attributes=[
            ("name", "object.name", lambda x: x.upper()),
            ("name", "object.fixed_value", "static_value"), 
        ]
    )
    def operation_with_attributes(self):
        return "Operation completed"
