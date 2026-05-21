import requests
from dotenv import load_dotenv
import os
from tabulate import tabulate  # Import tabulate for nice tables

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    models = data.get("data", [])

    # Prepare the data for the table
    table_data = []
    for model in models:
        # Extract specific fields
        model_id = model.get('id', 'N/A')
        owner = model.get('owned_by', 'N/A')
        active = "Yes" if model.get('active') else "No"
        
        # Format numbers with commas (e.g. 131072 -> 131,072)
        context = f"{model.get('context_window', 0):,}"
        max_tokens = f"{model.get('max_completion_tokens', 0):,}"

        table_data.append([model_id, owner, active, context, max_tokens])

    # Define table headers
    headers = ["Model ID", "Owned By", "Active", "Context Window", "Max Completion Tokens"]

    # Print the table using 'grid' format (looks like an Excel sheet)
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

else:
    print(f"Error: {response.status_code} - {response.text}")