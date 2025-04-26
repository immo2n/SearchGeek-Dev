from fastapi import FastAPI, Request
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re
import json

app = FastAPI()

# Load model once on startup
model_name = "Qwen/Qwen2.5-3B"
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True)
device = torch.device("cpu")
model.to(device)

class PromptRequest(BaseModel):
    prompt: str
    max_tokens: int = 100

@app.post("/generate")
def generate(request: PromptRequest):
    inputs = tokenizer(request.prompt, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_new_tokens=request.max_tokens, pad_token_id=tokenizer.eos_token_id)
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract ALL JSON-like objects
    matches = re.findall(r"\{[\s\S]*?\}", text)

    if matches:
        # Try parsing the LAST match (most likely the real one)
        for json_text in reversed(matches):
            try:
                parsed_json = json.loads(json_text)
                return {"response": parsed_json}
            except json.JSONDecodeError:
                continue
        return {"error": "No valid JSON found", "raw_response": text}
    else:
        return {"error": "No JSON found", "raw_response": text}
