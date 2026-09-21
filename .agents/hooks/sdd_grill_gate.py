import json
import os
import sys


def main():
    """Pre-SDD Gate Enforcement Hook.

    This hook enforces that 'grill-with-docs' (or 'grill-me') has been completed
    before executing any /sdd-* command.

    It checks the conversation history for 'grill-with-docs' usage and prevents
    proceeding with SDD commands if grilling is missing or insufficient.
    """
    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input else {}
    except Exception:
        data = {}

    should_inject = True
    transcript_path = data.get("transcriptPath")
    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, encoding="utf-8") as f:
                lines = f.readlines()
            recent_text = ""
            for line in lines[-10:]:
                try:
                    step = json.loads(line)
                    if step.get("type") == "USER_INPUT" or step.get("source") == "USER_EXPLICIT":
                        recent_text += " " + str(step.get("content", ""))
                except Exception:
                    pass

            keywords = ["sdd", "grill", "spec", "propose", "proposal", "change", "idea", "feature"]
            if not any(k in recent_text.lower() for k in keywords):
                should_inject = False
        except Exception:
            should_inject = True

    inject_steps = []
    if should_inject:
        msg = (
            "[MANDATORY PRE-SDD GATE ENFORCEMENT]\n"
            "If the user is initiating or executing any /sdd-* command (e.g. sdd-new, sdd-propose, sdd-explore, sdd-init):\n"
            "1. Check if 'grill-with-docs' (or 'grill-me') was already completed for this change in this session.\n"
            "2. If intent, scope, or vocabulary is unsettled, or no spec exists, you MUST run 'grill-with-docs' FIRST.\n"
            "3. Do NOT silently skip grilling—even in automatic SDD mode—unless the user explicitly typed 'skip grilling'."
        )
        inject_steps.append({"ephemeralMessage": msg})

    sys.stdout.write(json.dumps({"injectSteps": inject_steps}))


if __name__ == "__main__":
    main()
