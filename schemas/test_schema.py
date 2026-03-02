import json
import os
import jsonschema

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def test_schema_validation():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load schemas
    claim_schema_path = os.path.join(base_dir, "claim.schema.json")
    report_schema_path = os.path.join(base_dir, "research_report.schema.json")
    example_path = os.path.join(base_dir, "example_report.json")
    
    claim_schema = load_json(claim_schema_path)
    report_schema = load_json(report_schema_path)
    example_data = load_json(example_path)
    
    try:
        # Lint schemas
        jsonschema.Draft7Validator.check_schema(claim_schema)
        jsonschema.Draft7Validator.check_schema(report_schema)
        print("Linting Successful! Schemas are valid Draft-07 schemas.")
    except jsonschema.exceptions.SchemaError as e:
        print(f"Schema Linting Failed: {e.message}")
        exit(1)
        
    # Set up schema store for resolving references using Registry
    from referencing import Registry, Resource
    registry = Registry().with_resource(claim_schema['$id'], Resource.from_contents(claim_schema))
    
    # Validate the example data against the research report schema
    try:
        validator = jsonschema.Draft7Validator(report_schema, registry=registry)
        validator.validate(example_data)
        print("Validation Successful! The example data adheres to the ResearchReport schema.")
    except jsonschema.exceptions.ValidationError as e:
        print("Validation Failed!")
        print(f"Error Message: {e.message}")
        print(f"Failed at path: {' -> '.join([str(p) for p in e.path])}")
        exit(1)

if __name__ == "__main__":
    test_schema_validation()
