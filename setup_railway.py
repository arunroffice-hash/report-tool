import requests
import json

API_TOKEN = "57afd43a-7bdd-423e-8426-2c8df3852e15"
PROJECT_ID = "cd113e44-d402-4381-8c3d-397c4957eb04"
ENVIRONMENT_ID = "734008c9-a177-4b01-aa11-b34fc9f81b0e"
ENDPOINT = "https://backboard.railway.com/graphql/v2"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

print("="*60)
print("RAILWAY POSTGRESQL AUTO-SETUP")
print("="*60)

# Step 1: Verify token
query_me = """
{
  me {
    id
    email
  }
}
"""

print("\n1️⃣ Verifying API token...")
response = requests.post(ENDPOINT, headers=headers, json={"query": query_me})
result = response.json()

if "data" in result and result["data"].get("me"):
    print("✅ Token verified! Email:", result["data"]["me"]["email"])
else:
    print("❌ Token failed:", result)
    exit(1)

# Step 2: Get project details
query_project = """
{
  project(id: "%s") {
    id
    name
  }
}
""" % PROJECT_ID

print("\n2️⃣ Fetching project details...")
response = requests.post(ENDPOINT, headers=headers, json={"query": query_project})
result = response.json()

if "data" in result and result["data"].get("project"):
    project = result["data"]["project"]
    print(f"✅ Project found: {project['name']} ({project['id']})")
else:
    print("⚠️ Could not fetch project:", result)

# Step 3: Try creating PostgreSQL service via serviceCreate
query_service = """
mutation {
  serviceCreate(
    input: {
      projectId: "%s"
      environmentId: "%s"
      name: "postgres"
      source: {
        image: "postgres:15"
      }
    }
  ) {
    service {
      id
      name
    }
  }
}
""" % (PROJECT_ID, ENVIRONMENT_ID)

print("\n3️⃣ Attempting to create PostgreSQL service...")
response = requests.post(ENDPOINT, headers=headers, json={"query": query_service})
result = response.json()
print(json.dumps(result, indent=2))

if "data" in result and result["data"].get("serviceCreate"):
    service = result["data"]["serviceCreate"]["service"]
    print(f"\n✅ PostgreSQL service created!")
    print(f"Service ID: {service['id']}")
    print(f"Service Name: {service['name']}")
else:
    print("\n⚠️ ServiceCreate approach failed, trying alternative...")
    
    # Step 4: Alternative - Try plugin approach with full permissions query
    query_plugin_v2 = """
    mutation {
      pluginCreate(
        input: {
          projectId: "%s"
          environmentId: "%s"
          name: "postgres"
        }
      ) {
        id
        name
      }
    }
    """ % (PROJECT_ID, ENVIRONMENT_ID)
    
    print("\n4️⃣ Trying pluginCreate with environment ID...")
    response = requests.post(ENDPOINT, headers=headers, json={"query": query_plugin_v2})
    result = response.json()
    print(json.dumps(result, indent=2))
    
    if "data" in result and result["data"].get("pluginCreate"):
        plugin = result["data"]["pluginCreate"]
        print(f"\n✅ PostgreSQL plugin created!")
        print(f"Plugin ID: {plugin['id']}")
        print(f"Plugin Name: {plugin['name']}")
    else:
        print("\n❌ All automated approaches failed")
        print("Error details:", result)

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("1. Go to: https://railway.app/project/" + PROJECT_ID)
print("2. Click '+ New' → 'Database' → 'PostgreSQL'")
print("3. Click 'Redeploy latest'")
print("="*60)
