import os

SKIP_DIRS = {".git", "venv", "__pycache__", "uploads"}
EXTENSIONS = {".py", ".html", ".css", ".js", ".txt", ".json"}

def is_emoji(character):
    code = ord(character)

    return (
        0x1F000 <= code <= 0x1FAFF
        or 0x1FC00 <= code <= 0x1FFFF
        or 0x2600 <= code <= 0x27BF
        or 0x2300 <= code <= 0x23FF
    )

found = False

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for filename in files:
        if os.path.splitext(filename)[1].lower() not in EXTENSIONS:
            continue

        filepath = os.path.join(root, filename)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
        except Exception:
            continue

        emojis = sorted(set(character for character in content if is_emoji(character)))

        if emojis:
            found = True
            print()
            print(filepath)
            print("  Emojis:", " ".join(emojis))

if not found:
    print("No emojis found.")

print()
print("Scan complete.")