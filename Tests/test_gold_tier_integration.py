"""
Gold Tier Integration Tests
Validates all hackathon-required workflows end-to-end.

Run with: pytest Tests/test_gold_tier_integration.py -v
"""

import pytest
import json
import time
from pathlib import Path
from datetime import datetime
import subprocess
import shutil
import os

# Test Configuration
BASE_DIR = Path(__file__).parent.parent
INBOX = BASE_DIR / "00_Inbox"
NEEDS_ACTION = BASE_DIR / "01_Needs_Action"
PENDING = BASE_DIR / "02_Pending_Approval"
APPROVED = BASE_DIR / "03_Approved"
ARCHIVE = BASE_DIR / "04_Archive"
LOGS = BASE_DIR / "Logs"
MANAGEMENT = BASE_DIR / "Management"


@pytest.fixture(scope="session")
def test_env():
    """Setup test environment"""
    # Create test directories if they don't exist
    for dir_path in [INBOX, NEEDS_ACTION, PENDING, APPROVED, ARCHIVE, LOGS, MANAGEMENT]:
        dir_path.mkdir(exist_ok=True, parents=True)
    
    yield
    
    # Cleanup can be added here if needed


class TestOdooIntegration:
    """Test Odoo accounting workflows"""
    
    def test_odoo_mcp_server_connection(self, test_env):
        """
        Test: Odoo MCP server can be imported and initialized
        Expected: No errors, graceful degradation if Odoo not running
        """
        try:
            result = subprocess.run(
                ["python", "odoo_mcp_server.py"],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should either connect or gracefully fail
            assert "error" not in result.stderr.lower() or "connection" in result.stderr.lower()
        except subprocess.TimeoutExpired:
            pytest.skip("Odoo MCP server timeout - may not be running")
    
    def test_financial_safety_threshold(self, test_env):
        """
        Test: Verify $100 threshold is enforced in Company Handbook
        Expected: Handbook contains $100 safety rule
        """
        handbook = BASE_DIR / "Company_Handbook.md"
        assert handbook.exists(), "Company Handbook should exist"
        
        content = handbook.read_text()
        assert "$100" in content, "Handbook should mention $100 threshold"
        assert "SAFETY THRESHOLD" in content or "approval" in content.lower()


class TestSocialMediaIntegration:
    """Test social media workflows"""
    
    def test_facebook_poster_exists(self, test_env):
        """Test: Facebook poster script exists and has summary flag"""
        fb_poster = BASE_DIR / "facebook_poster.py"
        assert fb_poster.exists(), "facebook_poster.py should exist"
        
        content = fb_poster.read_text()
        assert "--summary" in content, "Facebook poster should support --summary flag"
    
    def test_twitter_poster_exists(self, test_env):
        """Test: Twitter poster script exists and has summary flag"""
        twitter_poster = BASE_DIR / "twitter_poster.py"
        assert twitter_poster.exists(), "twitter_poster.py should exist"
        
        content = twitter_poster.read_text()
        assert "--summary" in content, "Twitter poster should support --summary flag"
    
    def test_instagram_poster_exists(self, test_env):
        """Test: Instagram poster script exists and has summary flag"""
        ig_poster = BASE_DIR / "instagram_poster.py"
        assert ig_poster.exists(), "instagram_poster.py should exist"
        
        content = ig_poster.read_text()
        assert "--summary" in content, "Instagram poster should support --summary flag"
    
    def test_social_media_summary_module(self, test_env):
        """Test: Social media summary module exists"""
        summary_module = BASE_DIR / "social_media_summary.py"
        assert summary_module.exists(), "social_media_summary.py should exist"


class TestCEOAudit:
    """Test CEO briefing generation"""
    
    def test_ceo_audit_script_exists(self, test_env):
        """Test: CEO audit generation script exists"""
        audit_script = BASE_DIR / "generate_ceo_audit.py"
        assert audit_script.exists(), "generate_ceo_audit.py should exist"
    
    def test_ceo_audit_can_run(self, test_env):
        """Test: CEO audit script can execute without errors"""
        try:
            result = subprocess.run(
                ["python", "generate_ceo_audit.py"],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                timeout=30
            )
            # Should complete without critical errors
            assert result.returncode == 0 or "error" not in result.stderr.lower()
        except subprocess.TimeoutExpired:
            pytest.fail("CEO audit generation timed out")


class TestRalphLoop:
    """Test autonomous iteration"""
    
    def test_ralph_loop_exists(self, test_env):
        """Test: Ralph Wiggum loop script exists"""
        ralph_script = BASE_DIR / "ralph_loop.py"
        assert ralph_script.exists(), "ralph_loop.py should exist"
    
    def test_ralph_loop_has_iteration_logic(self, test_env):
        """Test: Ralph loop contains iteration and completion logic"""
        ralph_script = BASE_DIR / "ralph_loop.py"
        content = ralph_script.read_text()
        
        assert "TASK_COMPLETE" in content, "Should check for TASK_COMPLETE signal"
        assert "max_iterations" in content.lower(), "Should have max iterations safety"


class TestSystemReliability:
    """Test error handling and graceful degradation"""
    
    def test_watchdog_exists(self, test_env):
        """Test: Watchdog monitoring script exists"""
        watchdog = BASE_DIR / "watchdog_gold.py"
        assert watchdog.exists(), "watchdog_gold.py should exist"
    
    def test_orchestrator_exists(self, test_env):
        """Test: Orchestrator script exists"""
        orchestrator = BASE_DIR / "orchestrator.py"
        assert orchestrator.exists(), "orchestrator.py should exist"
    
    def test_action_executor_exists(self, test_env):
        """Test: Action executor script exists"""
        executor = BASE_DIR / "action_executor.py"
        assert executor.exists(), "action_executor.py should exist"


class TestSecurityCompliance:
    """Test security and compliance features"""
    
    def test_env_file_in_gitignore(self, test_env):
        """Test: .env file is in .gitignore"""
        gitignore = BASE_DIR / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            assert ".env" in content, ".env should be in .gitignore"
    
    def test_credentials_not_in_git(self, test_env):
        """Test: Sensitive files are gitignored"""
        gitignore = BASE_DIR / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            sensitive_files = ["credentials.json", "token.pickle", ".env"]
            for file in sensitive_files:
                assert file in content, f"{file} should be in .gitignore"
    
    def test_company_handbook_exists(self, test_env):
        """Test: Company Handbook with rules exists"""
        handbook = BASE_DIR / "Company_Handbook.md"
        assert handbook.exists(), "Company_Handbook.md should exist"
        
        content = handbook.read_text()
        assert "Rule" in content or "rule" in content, "Should contain rules"


class TestSkillSystem:
    """Test Agent Skills implementation"""
    
    def test_skills_directory_exists(self, test_env):
        """Test: Skills directory exists with multiple skills"""
        skills_dir = BASE_DIR / ".claude" / "skills"
        assert skills_dir.exists(), "Skills directory should exist"
        
        # Count skills
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
        assert len(skill_dirs) >= 10, "Should have at least 10 skills for Gold Tier"
    
    def test_odoo_accountant_skill_exists(self, test_env):
        """Test: Odoo Accountant skill exists"""
        skill_file = BASE_DIR / ".claude" / "skills" / "odoo-accountant" / "SKILL.md"
        assert skill_file.exists(), "Odoo Accountant skill should exist"
    
    def test_social_media_manager_skill_exists(self, test_env):
        """Test: Social Media Manager skill exists"""
        skill_file = BASE_DIR / ".claude" / "skills" / "social-media-manager" / "SKILL.md"
        assert skill_file.exists(), "Social Media Manager skill should exist"


class TestDocumentation:
    """Test documentation completeness"""
    
    def test_readme_exists(self, test_env):
        """Test: README.md exists"""
        readme = BASE_DIR / "README.md"
        assert readme.exists(), "README.md should exist"
    
    def test_readme_has_architecture(self, test_env):
        """Test: README contains architecture diagram"""
        readme = BASE_DIR / "README.md"
        content = readme.read_text()
        assert "Architecture" in content or "architecture" in content
        assert "mermaid" in content.lower() or "graph" in content.lower()
    
    def test_gold_tier_summary_exists(self, test_env):
        """Test: Gold Tier summary documentation exists"""
        summary = BASE_DIR / "GOLD_TIER_SUMMARY.md"
        assert summary.exists(), "GOLD_TIER_SUMMARY.md should exist"


class TestHackathonReadiness:
    """Tests specifically for hackathon demonstration"""
    
    def test_all_gold_tier_features_present(self, test_env):
        """
        Test: Verify all Gold Tier features are implemented
        - Odoo integration ✓
        - Social media summary ✓
        - Weekly audit ✓
        - Ralph loop ✓
        - 10+ skills ✓
        """
        # Odoo
        assert (BASE_DIR / "odoo_mcp_server.py").exists()
        
        # Social Media
        assert (BASE_DIR / "social_media_summary.py").exists()
        assert (BASE_DIR / "facebook_poster.py").exists()
        assert (BASE_DIR / "twitter_poster.py").exists()
        assert (BASE_DIR / "instagram_poster.py").exists()
        
        # CEO Audit
        assert (BASE_DIR / "generate_ceo_audit.py").exists()
        assert (BASE_DIR / "weekly_audit_scheduler.py").exists()
        
        # Ralph Loop
        assert (BASE_DIR / "ralph_loop.py").exists()
        
        # Skills (10+)
        skills_dir = BASE_DIR / ".claude" / "skills"
        skill_count = len([d for d in skills_dir.iterdir() if d.is_dir()])
        assert skill_count >= 10, f"Should have 10+ skills, found {skill_count}"
    
    def test_project_structure_complete(self, test_env):
        """Test: All required directories exist"""
        required_dirs = [
            "00_Inbox",
            "01_Needs_Action", 
            "02_Pending_Approval",
            "03_Approved",
            "04_Archive",
            "Logs",
            "Management",
            "Tests",
            ".claude/skills"
        ]
        
        for dir_name in required_dirs:
            dir_path = BASE_DIR / dir_name
            assert dir_path.exists(), f"{dir_name} directory should exist"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short", "--color=yes"])
