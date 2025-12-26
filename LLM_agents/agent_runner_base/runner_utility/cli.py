def choose_agent(agents: list[str]) -> str:
    for i, a in enumerate(agents, 1):
        print(f"{i}. {a}")
    idx = int(input("Agent> "))
    return agents[idx - 1]