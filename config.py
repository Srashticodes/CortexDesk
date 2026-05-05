import yaml
import os
from dotenv import load_dotenv
load_dotenv()

def load_config():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})

    for service_name, details in services.items():
        # Load doc content
        doc_file = details.get("doc_file")
        if doc_file and os.path.exists(doc_file):
            with open(doc_file, "r") as f:
                details["docs"] = f.readlines()
        else:
            details["docs"] = []

        # Ensure description is a clean string (YAML block scalars add newlines)
        if "description" in details:
            details["description"] = " ".join(details["description"].split())

    return services

SERVICES = load_config()