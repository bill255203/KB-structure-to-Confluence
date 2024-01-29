import os
import json

# Get the directory of the Python script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the HTML file
html_file_path = os.path.join(script_directory, "simp.html")

# Read the HTML content from the HTML file
with open(html_file_path, "r") as file:
    html_content = file.read()

# Create the JSON payload
payload = {
    "version": {
        "number": 1,
        "message": "update"
    },
    "title": "Google Drive knowledge base 4",
    "type": "page",
    "body": {
        "storage": {
            "value": html_content,
            "representation": "storage"
        }
    }
}

# Save the JSON payload to a JSON file
json_file_path = "content.json"  # Replace with the desired JSON file path
with open(json_file_path, "w") as json_file:
    json.dump(payload, json_file, indent=4)

print(f"JSON payload has been saved to {json_file_path}")
