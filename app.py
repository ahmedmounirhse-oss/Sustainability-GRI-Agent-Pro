from src.ai_agent import SustainabilityAgent


def main() -> None:
    agent = SustainabilityAgent()

    print("=" * 60)
    print("Sustainability GRI AI Agent")
    print("Type your question in English.")
    print("Examples:")
    print("  - Show me the energy consumption KPIs for 2024")
    print("  - Provide a GRI-style narrative for water usage in 2023")
    print("  - Summarize GHG emissions in line with GRI 305 for 2025")
    print("Type 'q' or 'quit' to exit.")
    print("=" * 60)

    while True:
        query = input("\nYou: ").strip()
        if not query:
            continue

        if query.lower() in {"q", "quit", "exit"}:
            print("\nAgent: Session ended. Goodbye.")
            break

        try:
            answer = agent.answer(query)
            print("\nAgent:\n")
            print(answer)
        except Exception as exc:
            print(f"\n[Error] {exc}")


if __name__ == "__main__":
    main()
