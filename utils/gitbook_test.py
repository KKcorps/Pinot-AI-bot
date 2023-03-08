import requests
import os
from dotenv import load_dotenv
load_dotenv(override=True)

# Set the GitBook API endpoint and access token
org_id = "foo"
endpoint = "https://api.gitbook.com/v1/orgs/" + org_id + "/search"
access_token = os.environ.get('GITBOOK_API_KEY', 'default_value')
# Define the search query and workspace
query = "upsert"
workspace = "bar"

# Set the search parameters
params = {
    "query": query
}

headers = {
    "Authorization" : "Bearer " + access_token
}

# Call the GitBook API search endpoint with the search parameters
response = requests.get(endpoint, params=params, headers=headers)

# Check for errors and print the search results
if response.status_code == 200:
    print(response.json())
    results = response.json()["results"]
    print(f"Found {len(results)} results matching the search query:")
    for result in results:
        print(f"{result['title']} ({result['url']})")
        break
else:
    print(f"Error: {response.status_code}")
