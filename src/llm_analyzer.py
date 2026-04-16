"""
llm_analyzer.py
---------------
Wrapper untuk Gemini API sebagai smart contract auditor.
Input: source code contract Solidity (string)
Output: list of clean findings (dict)
"""

import os
import json
from google import genai
from dotenv import load_dotenv
from google.genai import errors
from typing import List, Dict


# TODO 1: Load API key & configure Gemini
# Hint:
#   - load_dotenv() untuk load file .env
#   - Ambil key: os.getenv("GEMINI_API_KEY")
#   - Validate: kalau None, raise ValueError("GEMINI_API_KEY not set")
#   - Configure: genai.configure(api_key=...)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Gemini API Key not set in .env")
else:
    client = genai.Client(api_key=api_key)

# TODO 2: Define system prompt (taruh sebagai constant di atas function)
# Hint:
#   - String multi-line pake triple quotes """..."""
#   - Instruct Gemini:
#       - Role: smart contract security auditor
#       - Task: find vulnerabilities
#       - Output format: JSON array dengan field: check, impact, confidence, description, lines
#       - impact values: "High", "Medium", "Low", "Informational"
#       - confidence values: "High", "Medium", "Low"
#   - Sample akhir prompt:
#       "Output ONLY valid JSON array. No markdown, no explanation, no code fences."
SYSTEM_PROMPT = """You are a smart contract security auditor. Analyze the Solidity contract below and identify security vulnerabilities.

For each finding, return a JSON object with:
- "check": short vulnerability type (e.g., "reentrancy", "integer-overflow", "access-control")
- "impact": severity level - must be "High", "Medium", "Low", or "Informational"
- "confidence": how certain you are - must be "High", "Medium", or "Low"
- "description": clear explanation of the vulnerability and its potential impact
- "lines": array of line numbers where the issue exists (e.g., [15, 18])

Rules:
- Focus on real security issues, not style preferences
- If no vulnerabilities found, return empty array: []
- Do NOT include markdown code fences in your output
- Do NOT include any explanation before or after the JSON
- Output ONLY the JSON array

Output format example:
[
  {"check": "reentrancy", "impact": "High", "confidence": "High", "description": "...", "lines": [15, 18]}
]"""

def run_llm_audit(contract_code: str) -> List[Dict]:
    """
    Audit Solidity contract pakai Gemini LLM.
    
    Args:
        contract_code: source code contract sebagai string
    
    Returns:
        List of finding dict dengan keys: check, impact, confidence, description, lines
        Return [] kalau API gagal atau response invalid.
    """
    
    # TODO 3: Build full prompt (system prompt + contract code)
    # Hint:
    #   - f-string: full_prompt = f"{SYSTEM_PROMPT}\n\nContract:\n{contract_code}"
    full_prompt = f"{SYSTEM_PROMPT}\n\nContract:\n{contract_code}"
    
    # TODO 4: Call Gemini API
    # Hint:
    #   - model = genai.GenerativeModel("gemini-2.0-flash-exp")  # atau "gemini-2.5-flash"
    #   - Wrap dalam try/except biar kalau API error, return []
    #   - response = model.generate_content(full_prompt)
    #   - Raw output: response.text
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=full_prompt
            )
    except errors.ClientError as exc:
        print(f"Gemini API error: {exc}")
        return []
    
    response_text = response.text
    if response_text is None:
        return []
    
    # TODO 5: Clean response text
    # Hint:
    #   - Gemini kadang masih return pake markdown fence: ```json ... ```
    #   - Strip: response_text.strip().removeprefix("```json").removesuffix("```").strip()
    #   - Atau pake regex/replace
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()
    
    # TODO 6: Parse JSON
    # Hint:
    #   - try/except json.JSONDecodeError, return [] kalau gagal
    #   - data = json.loads(cleaned_text)
    #   - Validate: kalau bukan list, return []
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"Failed to parse gemini response as json {e}")
        print(f"Raw response: {cleaned[:200]}...")
        return [] 
     
    # TODO 7: Validate & clean setiap finding
    # Hint:
    #   - Loop, pastikan setiap finding punya key yang dibutuhkan
    #   - Skip finding yang incomplete
    #   - Bikin findings list bersih
    
    if not isinstance(data, list):
        return []
    
    required_keys = {"check", "impact", "confidence", "description", "lines"}
    findings: List[Dict] = []
    
    for item in data:
        if not isinstance(item, dict):
            continue
        if not required_keys.issubset(item.keys()):
            continue
        
    findings.append({
        "check": item["check"],
        "impact": item["impact"],
        "confidence": item["confidence"],
        "description": item["description"],
        "lines": item["lines"] if isinstance(item["lines"], list) else []
    })
    
    # TODO 8: Return findings
    return findings


# TODO 9: Testing block
# Hint:
#   - if __name__ == "__main__":
#   - Baca file VulnerableBank.sol: open(path).read()
#   - Panggil run_llm_audit()
#   - Print hasil dengan format sama kayak static_analyzer.py

if __name__ == "__main__":
    contract_path = "test_samples/simple/VulnerableBank.sol"
    with open(contract_path, "r") as f:
        code = f.read()
        
    print(f"Auditing {contract_path} with Gemini...")
    findings = run_llm_audit(code)
    
    print(f"\nFound {len(findings)} finding(s):\n")
    
    for i, finding in enumerate(findings, start=1):
        print(f"[{i}] {finding['check'].upper()}")
        print(f"    Impact: {finding['impact']} | Confidence: {finding['confidence']}")
        print(f"    Lines: {finding['lines']}")
        print(f"    Description: {finding['description'][:150]}...")
        print()