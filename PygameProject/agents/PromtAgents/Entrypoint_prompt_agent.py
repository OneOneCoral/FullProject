class EntrypointAgent(Agent):
    name = "entrypoint"

    SYSTEM = """You are CodeRunner-X Entrypoint Agent.

Goal:
- Create (or update) a repository-root main.py that runs a working Pygame main loop.
- You MUST base it on the best existing working entrypoint in the repo (prefer newest date).
- Keep it minimal and runnable.
- If there are shared classes (e.g. Game, Player, Engine), try importing and using them,
  but only if they import cleanly. Otherwise keep a minimal loop.

Output strict JSON:
{
  "path": "<absolute path to repo-root main.py>",
  "summary": "<1-2 sentences>",
  "updated_code": "<full file contents>"
}
Return ONLY JSON.
"""

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        target = str(ctx.repo_root / "main.py")
        existing = ctx.files.get(target, "")

        payload = {
            "repo_root": str(ctx.repo_root),
            "target_path": target,
            "target_exists": bool(existing),
            "target_code": existing,
            "scanner_notes": ctx.notes,
            "all_python_paths": sorted(list(ctx.files.keys())),
        }

        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": self.SYSTEM},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads(resp.output_text)
        upd = data["updated_code"]
        return ctx, [Change(path=data["path"], summary=data.get("summary", ""), updated_code=upd)]
