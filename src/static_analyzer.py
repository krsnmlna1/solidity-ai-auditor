"""
static_analyzer.py
------------------
Wrapper for the Slither static analyzer.
Input: path to a .sol file
Output: list of clean findings (dict)
"""

import subprocess
import json
from typing import List, Dict, Optional


def run_slither(contract_path: str) -> List[Dict]:
    """
    Run Slither on a Solidity contract and return a clean list of findings.
    
    Args:
        contract_path: Path to the .sol file (example: "test_samples/simple/VulnerableBank.sol")
    
    Returns:
        List of finding dicts. Each dict has these keys:
        - check (str): detector name, for example "reentrancy-eth"
        - impact (str): "High" / "Medium" / "Low" / "Informational"
        - confidence (str): "High" / "Medium" / "Low"
        - description (str): full description
        - lines (List[int]): list of line numbers in the contract
        
        If Slither fails or there are no findings, return an empty list [].
    """
    
    # Step 1: Run Slither via subprocess.
    # Hint:
    #   - Use subprocess.run()
    #   - Command: ["slither", contract_path, "--json", "-"]
    #     (the "-" means JSON output goes to stdout, not to a file)
    #   - Argument: capture_output=True, text=True
    #   - Save the result to a variable named `result`
    result = subprocess.run(
        ["slither", contract_path, "--json", "-"],
        capture_output=True, text=True
    )
    
    # Step 2: Handle the error case.
    # Hint:
    #   - If result.stdout is empty or None, return []
    #   - Slither may print errors to stderr while stdout stays empty
    #   - Use: if not result.stdout: return []
    if not result.stdout:
        return []

    # Step 3: Parse the JSON output.
    # Hint:
    #   - Use json.loads(result.stdout)
    #   - Store it in a variable named `data`
    #   - Structure: data["results"]["detectors"] is a list of raw findings
    #   - Wrap it in try/except json.JSONDecodeError and return [] if parsing fails
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    
    # Step 4: Extract the fields needed from each detector.
    # Hint:
    #   - Create an empty list: findings = []
    #   - Loop: for detector in data["results"]["detectors"]:
    #   - Each detector has: "check", "impact", "confidence", "description", "elements"
    #   - For "lines", take it from: detector["elements"][0]["source_mapping"]["lines"]
    #   - Append a clean dict to `findings`

    findings = []

    for detector in data["results"]["detectors"]:
        finding = {
            "check": detector["check"],
            "impact": detector["impact"],
            "confidence": detector["confidence"],
            "description": detector["description"],
            "elements": detector["elements"],
            "lines": detector["elements"][0]["source_mapping"]["lines"],
        }
        findings.append(finding)

    # Step 5: Return the findings.
    return findings


# Step 6 (bonus, for testing):
# Add an `if __name__ == "__main__":` block below
# that calls run_slither() with the path to your VulnerableBank.sol,
# then prints the results in a neat format.
if __name__ == "__main__":
    test_contract = "test_samples/simple/VulnerableBank.sol"

    print(f"Scanning {test_contract}...")
    findings = run_slither(test_contract)

    print(f"\nFound {len(findings)} finding(s):\n")

    for i, finding in enumerate(findings, start=1):
        print(f"[{i}] {finding['check'].upper()}")
        print(f"    Impact: {finding['impact']} | Confidence: {finding['confidence']}")
        print(f"    Lines: {finding['lines']}")
        print(f"    Description: {finding['description'][:100]}...")
        print()