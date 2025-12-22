



class CreateFileAgent(Agent):
    name = "create_file_test"

    def run(self, ctx: RepoContext) -> Tuple[RepoContext, List[Change]]:
        target = str(REPO_ROOT / "hello_from_agent.txt")
        content = "Hello from agent!\n=^.^=\n"

        ctx.notes.append(f"[create_file_test] would create: {target}")
        return ctx, [Change(path=target, summary="Create test file", updated_code=content)]
