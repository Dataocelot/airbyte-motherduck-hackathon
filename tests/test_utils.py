import json
import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from helper.utils import save_dict_to_json


def test_save_dict_to_json_success():
    """Test that the function saves data successfully to a JSON file."""
    # Test data
    data = {"name": "John", "age": 30, "city": "New York"}

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        file_path = temp_file.name  # Path to the temporary file

        # Call the function
        save_dict_to_json(data, file_path)

        # Verify file contents
        with open(file_path, "r") as json_file:
            saved_data = json.load(json_file)
        assert saved_data == data, "File contents do not match the original data."


def test_save_dict_to_json_invalid_data(capsys):
    """Test that the function handles invalid data gracefully."""
    # Test data
    invalid_data = set([1, 2, 3])  # JSON does not support sets

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        file_path = temp_file.name  # Path to the temporary file

        # Call the function
        save_dict_to_json(invalid_data, file_path)

        # Capture printed output
        captured = capsys.readouterr()
        assert (
            "Error saving data to JSON" in captured.out
        ), "Error message not printed as expected."

        # Verify the file was not corrupted
        with open(file_path, "r") as temp_file:
            assert temp_file.read() == "", "Temporary file should remain empty."


def test_save_dict_to_json_invalid_path(capsys):
    """Test that the function handles invalid file paths gracefully."""
    # Test data
    data = {"name": "John"}
    invalid_file_path = "/invalid_directory/test_data.json"  # Invalid path

    # Call the function
    save_dict_to_json(data, invalid_file_path)

    # Capture printed output
    captured = capsys.readouterr()
    assert (
        "Error saving data to JSON" in captured.out
    ), "Error message not printed for invalid path."
