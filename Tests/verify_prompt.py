from pathlib import Path
import sys

# Add parent dir to path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import InboxHandler

def test_prompt_generation():
    handler = InboxHandler()
    dummy_path = Path("c:/Users/Kashan/Documents/Digital labor/digital_labor2 - Copy/00_Inbox/test_task.md")
    
    prompt = handler._build_expert_prompt(dummy_path)
    
    print("\nGenerated Prompt:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    
    # Assertions
    assert "chief-of-staff.md" in prompt, "Missing reference to Chief of Staff skill"
    assert "STEP 1" in prompt, "Missing STEP 1"
    assert "01_Needs_Action/PLAN_" in prompt, "Missing Plan file instruction"
    assert "NARRATIVE PLAN" in prompt, "Missing Narrative Plan instruction"
    assert "lists the execution steps" in prompt, "Missing 'list steps' instruction"
    assert "STEP 3: ONLY AFTER the plan is written" in prompt, "Missing sequential enforcement"
    
    print("\nSUCCESS: Prompt contains all required elements.")

if __name__ == "__main__":
    test_prompt_generation()
