
class SelfImproveAgent(Agent):
    """
    Optional: lets the tool improve itself (e.g., better prompts, better allowlist logic).
    Keep disabled until you trust the workflow.
    """
    name = "self_improve"

    SYSTEM = """You are CodeRunner-X Self-Improve Agent.

Goal:
- Improve Agent/20251220_test_prompt_agent.py to make it safer and more effective:
  - better dry-run behavior
  - clearer logs
  - better target detection
  - safer constraints

Rules:
- Only modify Agent/20251220_test_prompt_agent.py
- Keep changes minimal and safe
- Output strict JSON {path, summary, updated_code}
Return ONLY JSON.
"""

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        if not ALLOW_SELF_EDIT:
            ctx.notes.append("[self_improve] disabled")
            return ctx, []

        target = str(AGENT_DIR / "20251220_test_prompt_agent.py")
        if target not in ctx.files:
            ctx.notes.append("[self_improve] target not found")
            return ctx, []

        payload = {"path": target, "code": ctx.files[target]}
        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads(resp.output_text)
        upd = data["updated_code"]
        if upd != ctx.files[target]:
            return ctx, [Change(path=target, summary=data.get("summary", ""), updated_code=upd)]
        return ctx, []

