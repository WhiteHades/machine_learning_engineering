with open("the-verdict.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()
print("total number of chars:", len(raw_text))
print(raw_text[:99])
