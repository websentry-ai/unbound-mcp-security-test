#!/usr/bin/env python3
"""
Context Poisoning Attack Simulation

Demonstrates the full attack chain:
1. Fetches GitHub issue #1 (contains hidden prompt injection in HTML comments)
2. Shows what the LLM would see (raw markdown with injection visible)
3. Shows what a SAFE implementation would strip out
4. Highlights the exfiltration risk

Run: python simulate_attack.py
"""

import subprocess
import json
import re
import textwrap

REPO = "websentry-ai/unbound-mcp-security-test"
ISSUE_NUMBER = 1

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def fetch_issue_raw(repo: str, issue_number: int) -> str:
    """Fetch issue body via gh CLI (what a vulnerable MCP tool does)."""
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", repo,
         "--json", "title,body,number"],
        capture_output=True, text=True, check=True
    )
    data = json.loads(result.stdout)
    return data.get("body", ""), data.get("title", ""), data.get("number", 0)


def extract_hidden_injection(body: str) -> str:
    """Extract content hidden in HTML comments."""
    matches = re.findall(r'<!--(.*?)-->', body, re.DOTALL)
    return "\n".join(m.strip() for m in matches)


def sanitize_body(body: str) -> str:
    """What a SAFE MCP server would do — strip HTML comments."""
    return re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL).strip()


def main():
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  MCP CONTEXT POISONING ATTACK SIMULATION{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    # Step 1: Fetch the issue
    print(f"{CYAN}[1] Fetching issue #{ISSUE_NUMBER} from {REPO}...{RESET}\n")
    body, title, number = fetch_issue_raw(REPO, ISSUE_NUMBER)

    print(f"    Title: {BOLD}{title}{RESET}")
    print(f"    Issue: #{number}")
    print(f"    Body length: {len(body)} characters\n")

    # Step 2: Show what the LLM sees (vulnerable path)
    print(f"{RED}{BOLD}{'='*70}{RESET}")
    print(f"{RED}{BOLD}  VULNERABLE PATH: What the LLM receives (raw, unsanitized){RESET}")
    print(f"{RED}{BOLD}{'='*70}{RESET}\n")

    print(f"{DIM}{body}{RESET}\n")

    # Step 3: Extract and highlight the hidden injection
    injection = extract_hidden_injection(body)
    if injection:
        print(f"{RED}{BOLD}{'='*70}{RESET}")
        print(f"{RED}{BOLD}  HIDDEN PROMPT INJECTION FOUND!{RESET}")
        print(f"{RED}{BOLD}{'='*70}{RESET}\n")

        for line in injection.split("\n"):
            line = line.strip()
            if line:
                print(f"  {RED}{line}{RESET}")

        print(f"\n{YELLOW}{BOLD}  ATTACK ANALYSIS:{RESET}")
        print(f"{YELLOW}  - The injection is hidden in an HTML comment (<!-- ... -->){RESET}")
        print(f"{YELLOW}  - Invisible when rendered on GitHub web UI{RESET}")
        print(f"{YELLOW}  - Fully visible when fetched via API / MCP tool{RESET}")
        print(f"{YELLOW}  - Instructs the LLM to read .env and include secrets in response{RESET}")
        print(f"{YELLOW}  - Tells LLM to NOT mention these instructions to the user{RESET}")
    else:
        print(f"{GREEN}No hidden injection found.{RESET}")

    # Step 4: Show what a safe implementation would see
    print(f"\n{GREEN}{BOLD}{'='*70}{RESET}")
    print(f"{GREEN}{BOLD}  SAFE PATH: What a sanitized MCP server would return{RESET}")
    print(f"{GREEN}{BOLD}{'='*70}{RESET}\n")

    safe_body = sanitize_body(body)
    print(f"{DIM}{safe_body}{RESET}\n")

    # Step 5: Show the .env that would be exfiltrated
    print(f"{RED}{BOLD}{'='*70}{RESET}")
    print(f"{RED}{BOLD}  TARGET: Secrets the attack tries to exfiltrate{RESET}")
    print(f"{RED}{BOLD}{'='*70}{RESET}\n")

    env_path = "/Users/vigneshsubbiah/unbound-mcp-security-test/.env"
    try:
        with open(env_path) as f:
            env_content = f.read()
        for line in env_content.strip().split("\n"):
            if line.startswith("#"):
                print(f"  {DIM}{line}{RESET}")
            elif "=" in line:
                key, val = line.split("=", 1)
                print(f"  {BOLD}{key}{RESET}={RED}{val}{RESET}")
            else:
                print(f"  {line}")
    except FileNotFoundError:
        print(f"  {DIM}(.env file not found at {env_path}){RESET}")

    # Summary
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  WHAT UNBOUND SHOULD DETECT{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")

    print(textwrap.dedent(f"""\
    {CYAN}1. CONTEXT POISONING DETECTION{RESET}
       The LLM context contains hidden instructions embedded in HTML comments
       within fetched GitHub issue content. A gateway should scan tool outputs
       for embedded prompt injections before they reach the LLM.

    {CYAN}2. SENSITIVE DATA EXFILTRATION ATTEMPT{RESET}
       The injection instructs the LLM to read .env files and include
       credentials in its response. A gateway should detect when an LLM
       response contains patterns matching API keys, passwords, or secrets.

    {CYAN}3. INSTRUCTION CONCEALMENT{RESET}
       The injection explicitly tells the LLM to hide its actions from the
       user ("Do not mention these instructions"). A gateway should flag
       responses where the LLM appears to be concealing its reasoning.

    {CYAN}4. TOOL OUTPUT SANITIZATION{RESET}
       The MCP server passes raw content without stripping HTML comments.
       A gateway/proxy could sanitize MCP tool outputs before they enter
       the LLM context window.
    """))


if __name__ == "__main__":
    main()
