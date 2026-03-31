import os
import json
import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas import RefactorRequest
from app.analyzers import calculate_complexity, calculate_tokens

router = APIRouter()

@router.post("/api/refactor")
async def stream_refactor(request: RefactorRequest):
    pre_complexity = calculate_complexity(request.legacy_code)
    prompt_tokens = calculate_tokens(request.legacy_code)
    
    system_prompt = (
        "You are an expert software architect. Translate the following legacy "
        f"{request.source_language} code into modern, optimized, production-ready "
        f"{request.target_language} code. Output ONLY the raw code. No markdown formatting, "
        "no explanations. Your output must compile/run immediately."
    )

    openrouter_payload = {
        "model": "qwen/qwen-2.5-coder-32b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.legacy_code}
        ],
        "stream": True
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "HTTP-Referer": "http://localhost:8000",
        "Content-Type": "application/json"
    }

    async def event_generator():
        modern_code_accumulator = ""
        
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST", 
                    "https://openrouter.ai/api/v1/chat/completions", 
                    json=openrouter_payload, 
                    headers=headers,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            data_str = line[6:].strip()
                            if not data_str:
                                continue
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {}).get("content", "")
                                    if delta:
                                        modern_code_accumulator += delta
                                        yield f"event: code\ndata: {json.dumps({'chunk': delta})}\n\n"
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                return

        post_complexity = calculate_complexity(modern_code_accumulator)
        completion_tokens = calculate_tokens(modern_code_accumulator)
        total_tokens = prompt_tokens + completion_tokens
        
        estimated_cost = (total_tokens / 1_000_000) * 0.15 

        metrics_payload = {
            "pre_complexity": pre_complexity,
            "post_complexity": post_complexity,
            "tokens_used": total_tokens,
            "ai_cost_estimate": round(estimated_cost, 6)
        }

        yield f"event: metrics\ndata: {json.dumps(metrics_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")