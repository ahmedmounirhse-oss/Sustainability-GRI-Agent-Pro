from src.data_loader import load_indicator
from src.reporting import build_indicator_narrative

def main():
    df = load_indicator("water")

    print("\n=== WATER GRI NARRATIVE ===\n")
    text = build_indicator_narrative("water", df, 2024)
    print(text)

if __name__ == "__main__":
    main()
