"""
auditor.py
----------
Main orchestrator: combine Slither + Gemini into one unified audit report.
Input: path to a .sol file
Output: dict containing metadata + combined findings
"""

from typing import List, Dict
from static_analyzer import run_slither
from llm_analyzer import run_llm_audit
from formatter import save_json_report, save_markdown_report


def audit_contract(contract_path: str) -> Dict:
    """
    Full audit pipeline: Slither (static) + Gemini (LLM).
    
    Args:
        contract_path: path to the .sol file
    
    Returns:
        Dict with keys:
        - contract: file name
        - total_findings: total count
        - findings: list of all findings (Slither + Gemini)
    """
    
    # TODO 1: Run Slither
    # Hint:
    #   - Call run_slither(contract_path)
    #   - Store in variable slither_findings
    #   - Add field "source": "slither" to each finding
    #   - Use loop: for finding in slither_findings: finding["source"] = "slither"
    slither_findings = run_slither(contract_path)
    for finding in slither_findings:
        finding["source"] = "slither"
    
    
    # TODO 2: Read contract file -> as string
    # Hint:
    #   - with open(contract_path, "r") as f: code = f.read()
    #   - Wrap in try/except FileNotFoundError
    #   - If file does not exist, set code = None
    try:
        with open(contract_path, "r") as f:
            code = f.read()    
    except FileNotFoundError as exc:
        print(f"File is empty/missing: {contract_path}")
        code = None
        
    # after reading file
    # TODO 3: Run Gemini (if code is successfully read)
    # Hint:
    #   - If code is not None: call run_llm_audit(code)
    #   - Store in gemini_findings
    #   - Add field "source": "gemini" to each finding
    #   - If code is None: gemini_findings = []
    if code is not None:
        gemini_findings = run_llm_audit(code)
        for finding in gemini_findings:
            finding["source"] = "gemini"
    else:
        gemini_findings = []
    
    
    # TODO 4: Combine findings
    # Hint:
    #   - all_findings = slither_findings + gemini_findings
    all_findings = slither_findings + gemini_findings
    
    
    # TODO 5: Build report dict
    # Hint:
    #   - return {
    #       "contract": contract_path,
    #       "total_findings": len(all_findings),
    #       "slither_count": len(slither_findings),
    #       "gemini_count": len(gemini_findings),
    #       "findings": all_findings
    #   }
    return {
          "contract": contract_path,
          "total_findings": len(all_findings),
          "slither_count": len(slither_findings),
          "gemini_count": len(gemini_findings),
          "findings": all_findings
    }


# TODO 6: Testing block
# Hint:
#   - if __name__ == "__main__":
#   - Call audit_contract("test_samples/simple/VulnerableBank.sol")
#   - Print summary: total findings, per source
#   - Loop and print each finding (same format as before)
#   - Add print finding["source"] so the source is visible

if __name__ == "__main__":
    contract = "test_samples/simple/VulnerableBank.sol"
    
    print(f"Running full audit on {contract}...\n")
    
    report = audit_contract(contract)
    
    print(f"Total findings: {report['total_findings']}")
    print(f"  Slither: {report['slither_count']}")
    print(f"  Gemini:  {report['gemini_count']}")
    print(f"\n{'='*60}\n")
    
    for i, finding in enumerate(report["findings"], start=1):
        print(f"[{i}] [{finding['source'].upper()}] {finding['check'].upper()}")
        print(f"    Impact: {finding['impact']} | Confidence: {finding['confidence']}")
        print(f"    Lines: {finding['lines']}")
        print(f"    Description: {finding['description'][:150]}...")
        print()
        
    json_path = save_json_report(report)
    md_path = save_markdown_report(report)
    
    print(f"\nReports saved:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")