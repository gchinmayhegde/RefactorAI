import asyncio
import httpx
import json

async def test_refactor_stream():
    url = "http://localhost:8000/api/refactor"
    
    legacy_code = """
def process_data(data):
    if data:
        if type(data) == list:
            results = []
            for item in data:
                if item != None:
                    if str(item).isdigit():
                        results.append(int(item))
            return results
        else:
            return None
    return None
"""

    payload = {
        "legacy_code": legacy_code.strip(),
        "source_language": "python",
        "target_language": "python"
    }
    
    print("🚀 Sending request to RefactorAI Pipeline...\n")
    print("--- STREAMING CODE ---")
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("POST", url, json=payload, timeout=60.0) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("event: code"):
                        data = json.loads(line.split("data: ")[1])
                        print(data['chunk'], end="", flush=True)
                        
                    elif line.startswith("event: metrics"):
                        print("\n\n--- FINOPS METRICS ---")
                        metrics = json.loads(line.split("data: ")[1])
                        print(json.dumps(metrics, indent=2))
                        
                    elif line.startswith("event: error"):
                        print(f"\n\n❌ ERROR: {line}")
                        
        except httpx.HTTPError as e:
            print(f"\nHTTP Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_refactor_stream())