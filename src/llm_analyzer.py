"""
llm_analyzer.py
---------------
Wrapper for Gemini API as a smart contract auditor.
Input: Solidity contract source code (string)
Output: list of clean findings (dict)
"""

import os
import json
from google import genai
from dotenv import load_dotenv
from google.genai import errors
from typing import List, Dict


# Load API key and configure Gemini client.
# load_dotenv() loads variables from .env file.
# Validate that the key exists before creating client.
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Gemini API Key not set in .env")
else:
    client = genai.Client(api_key=api_key)

# System prompt for Gemini: instructs it to act as a security auditor
# and return findings in structured JSON format.
SYSTEM_PROMPT = """You are a smart contract security auditor. Analyze the Solidity contract below and identify security vulnerabilities.

For each finding, return a JSON object with:
- "check": short vulnerability type (e.g., "reentrancy", "integer-overflow", "access-control")
- "impact": severity level - must be "High", "Medium", "Low", or "Informational"
- "confidence": how certain you are - must be "High", "Medium", or "Low"
- "description": clear explanation of the vulnerability and its potential impact
- "lines": array of line numbers where the issue exists (e.g., [15, 18])

Rules:
- Focus on real security issues, not style preferences
- Keep each description under 100 words
- Do NOT use special characters, newlines, or quotes inside JSON string values
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
    Audit a Solidity contract using Gemini LLM.
    
    Args:
        contract_code: Solidity contract source code as a string.
    
    Returns:
        List of finding dicts with keys: check, impact, confidence, description, lines.
        Returns an empty list [] if the API fails or the response is invalid.
    """
    
    # Build the full prompt by combining the system prompt with the contract code.
    full_prompt = f"{SYSTEM_PROMPT}\n\nContract:\n{contract_code}"
    
    # Call the Gemini API to generate the audit response.
    # Catch any API errors and return an empty list if the call fails.
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=full_prompt
        )
        response_text = response.text
    except errors.ClientError as exc:
        print(f"Gemini API error: {exc}")
        return []
    
    # Remove markdown code fences from the response (e.g., ```json ... ```).
    # Gemini may wrap JSON output in code fences; we strip them here.
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    # Fallback cleanup for common malformed JSON patterns in LLM output.
    cleaned = cleaned.replace("\n", " ")   # remove literal newlines
    cleaned = cleaned.replace("\\n", " ")  # remove escaped newlines
    cleaned = cleaned.replace("\t", " ")   # remove tabs
    
    # Parse the cleaned JSON response.
    # Catch JSON decode errors and validate that the result is a list.
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"Failed to parse gemini response as json {e}")
        print(f"Raw response: {cleaned[:200]}...")
        return [] 
     
    # Validate each finding and extract only the required fields.
    # Skip any findings that are incomplete or malformed.
    
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
    
    # Return the validated findings list.
    return findings


# Test block: reads a Solidity contract file and runs the audit.
# Prints results in a human-readable format.

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