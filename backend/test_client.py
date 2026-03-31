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
                
                current_event = None
                
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue # Skip empty spacing lines
                        
                    # 1. Catch the event type
                    if line.startswith("event:"):
                        current_event = line.split("event:")[1].strip()
                        
                    # 2. Catch the data payload for that event
                    elif line.startswith("data:"):
                        # Split only on the first occurrence of "data:" in case the JSON contains that word
                        data_str = line.split("data:", 1)[1].strip()
                        
                        if current_event == "code":
                            data = json.loads(data_str)
                            print(data.get('chunk', ''), end="", flush=True)
                            
                        elif current_event == "metrics":
                            print("\n\n--- FINOPS METRICS ---")
                            metrics = json.loads(data_str)
                            print(json.dumps(metrics, indent=2))
                            
                        elif current_event == "error":
                            print(f"\n\n❌ ERROR FROM PIPELINE: {data_str}")
                            
        except httpx.HTTPError as e:
            print(f"\nHTTP Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_refactor_stream())