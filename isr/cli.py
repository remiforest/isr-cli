#!/usr/bin/env python
"""
ISR CLI – Official command-line tool for the Intentional Software Representation methodology
https://github.com/remiforest/isr-cli
"""

import os
import sys
import subprocess
from pathlib import Path

import click

# Paths
ISR_PATH = Path("ISR.md")
TEMPLATES_DIR = Path(__file__).parent / "templates"
SYSTEM_PROMPT_TEMPLATE = TEMPLATES_DIR / "system_prompt.txt"

def load_isr() -> str:
    """Load the full ISR.md content – this is the single source of truth."""
    return ISR_PATH.read_text(encoding="utf-8") if ISR_PATH.exists() else "# ISR.md missing"

def get_code_summary() -> str:
    """Return a concise summary of all source files in the project (token-efficient)."""
    files = [p for p in Path('.').rglob('*') if p.is_file() and '.git' not in p.parts and 'venv' not in p.parts]
    summary = []
    for file_path in files[:50]:  # limit to avoid token explosion
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            truncated = content[:3000] + ("\n..." if len(content) > 3000 else "")
            summary.append(f"\n=== {file_path} ===\n{truncated}\n")
        except Exception:
            pass
    return "\n".join(summary)

def get_git_diff() -> str:
    """Return current unstaged + staged changes."""
    try:
        return subprocess.check_output(["git", "diff", "HEAD"]).decode("utf-8", errors="ignore")
    except Exception:
        return "No git diff available"

def call_llm(prompt: str, model: str) -> str:
    """Send prompt to Anthropic with full ISR context injected."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        click.echo("Error: ANTHROPIC_API_KEY environment variable is missing")
        sys.exit(1)

    import anthropic
    client = anthropic.Anthropic()

    formatted_system = SYSTEM_PROMPT_TEMPLATE.read_text(encoding="utf-8").format(
        isr_content=load_isr(),
        code_summary=get_code_summary(),
        git_diff=get_git_diff()
    )

    message = client.messages.create(
        model=model,
        max_tokens=8192,
        temperature=0.0,
        system=formatted_system,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

@click.group()
def cli():
    """ISR CLI – Keep your code perfectly aligned with its original intention."""
    pass

@cli.command()
@click.argument("prompt", nargs=-1)
@click.option("--model", "-m", default="claude-3-opus-20240229", help="Claude model to use")
def ask(prompt: tuple, model: str):
    """Ask anything – the LLM automatically receives the full ISR + current code context."""
    user_prompt = " ".join(prompt)
    if not user_prompt.strip():
        click.echo("Error: Please provide a prompt")
        return

    click.echo(f"Thinking Sending to {model} with full ISR context...")
    response = call_llm(user_prompt, model=model)
    click.echo("\n" + response)

@cli.command()
@click.option("--model", "-m", default="claude-3-opus-20240229")
def check(model: str):
    """Verify that current code strictly respects the ISR (invariants, glossary, workflows…)."""
    verification_prompt = """
You are an extremely strict architectural auditor.
Compare the current code against the ISR provided in the system prompt.
List EVERY drift, invariant violation, glossary misuse, or undocumented workflow change.
If everything is perfectly compliant, answer exactly: "ISR COMPLIANT ✅"
Otherwise, detail each issue with precise quotes from the ISR.
"""
    click.echo("Checking Verifying code ↔ ISR coherence...")
    response = call_llm(verification_prompt, model=model)
    click.echo("\n" + response)
    if "ISR COMPLIANT" not in response:
        sys.exit(1)  # perfect for CI/CD

if __name__ == "__main__":
    cli()