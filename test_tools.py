import sys
sys.path.append(".")
import tools

print("Tools loaded successfully!")
print(f"Total tools: {len(tools.TOOLS)}")

for name, tool in tools.TOOLS.items():
    print(f"Checking {name}...")
    func = tool.get("func")
    if not callable(func):
        print(f"ERROR: {name} does not have a callable func!")
