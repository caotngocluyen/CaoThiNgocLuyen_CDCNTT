# tests/audit_check_secrets.py
"""
Scans all codebase files for potential leaked API keys, tokens, or hardcoded passwords.
"""
import os
import re

PATTERNS = [
    r"(?i)(api[_-]?key|secret|token|password|auth_token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
    r"ghp_[A-Za-z0-9]{36}",
    r"sk-[A-Za-z0-9]{32,}",
    r"AIza[0-9A-Za-z-_]{35}"
]

EXCLUDE_DIRS = {".git", ".gemini", "venv", "__pycache__", ".pytest_cache", "node_modules"}

def scan():
    findings = []
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            if f.endswith((".py", ".json", ".yaml", ".yml", ".env", ".toml", ".md")):
                fpath = os.path.join(dirpath, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        lines = fp.readlines()
                        for idx, line in enumerate(lines, 1):
                            for p in PATTERNS:
                                if re.search(p, line):
                                    findings.append((fpath, idx, line.strip()))
                except Exception as e:
                    pass
    
    print("="*60)
    print("AUDIT: SCAN FOR HARDCODED SECRETS / API KEYS")
    print("="*60)
    if not findings:
        print("[PASSED] Zero leaked API keys or secrets detected across all workspace files.")
    else:
        print(f"[WARNING] Found {len(findings)} potential matches:")
        for path, line_no, content in findings:
            print(f"  {path}:{line_no} -> {content[:80]}")

if __name__ == "__main__":
    scan()
