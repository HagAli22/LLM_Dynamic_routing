"""Update .env with working API key"""

# Read current .env
try:
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print("Creating new .env file...")
    content = ""

# Working key
working_key = "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"

# Update keys
lines = []
found_openrouter = False
found_openai = False

for line in content.split('\n'):
    if line.startswith('OPENROUTER_API_KEY='):
        lines.append(f'OPENROUTER_API_KEY={working_key}')
        found_openrouter = True
    elif line.startswith('OPENAI_API_KEY='):
        if 'your_openrouter_key_here' in line or not line.split('=')[1].strip():
            lines.append(f'OPENAI_API_KEY={working_key}')
        else:
            lines.append(line)
        found_openai = True
    else:
        lines.append(line)

# Add if not found
if not found_openrouter:
    lines.insert(0, f'OPENROUTER_API_KEY={working_key}')
if not found_openai:
    lines.insert(1, f'OPENAI_API_KEY={working_key}')

# Write back
with open('.env', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("✅ .env file updated with working API key!")
print(f"🔑 OPENROUTER_API_KEY and OPENAI_API_KEY set to: {working_key[:30]}...")
