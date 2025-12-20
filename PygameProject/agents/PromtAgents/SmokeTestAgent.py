
class SmokeTestAgent(Agent):
    name = "smoke_test"

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        # Lightweight checks that don’t run the game:
        # - python -m py_compile on edited files (after edits are applied)
        # We run later; here just record intent.
        ctx.notes.append("[smoke_test] will run py_compile after apply")
        return ctx, []