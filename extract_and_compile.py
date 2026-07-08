import json
import os
import re

def clean_request(content):
    if content.startswith("<USER_REQUEST>\n"):
        content = content[len("<USER_REQUEST>\n"):]
    if content.endswith("\n</USER_REQUEST>"):
        content = content[:-len("\n</USER_REQUEST>")]
    return content

def main():
    curr_log_path = r"C:\Users\namir\.gemini\antigravity-ide\brain\9d3b5cfa-efc2-400d-84e6-addfd053ebcf\.system_generated\logs\transcript_full.jsonl"
    prev_log_path = r"C:\Users\namir\.gemini\antigravity-ide\brain\66c52d3e-6829-409a-a948-538c4aa70d32\.system_generated\logs\transcript_full.jsonl"
    readme_path = r"c:\Users\namir\OneDrive\Desktop\project S\README.md"
    results_path = r"c:\Users\namir\OneDrive\Desktop\project S\extracted_code.py"
    
    # 1. Extract Thesis Part 1 and Part 2 from current logs
    print("Extracting RealityOS Thesis and Research Plan...")
    part1 = None
    part2 = None
    
    if os.path.exists(curr_log_path):
        with open(curr_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    content = data.get("content", "")
                    if "RealityOS — An Event-Driven Computational Substrate for Intelligence" in content and "The Thesis" in content:
                        part1 = clean_request(content)
                    if "Below is a complete, reviewer" in content and "Theorem" in content:
                        part2 = clean_request(content)
                except Exception as e:
                    continue
                    
    if not part1:
        print("Warning: Could not find Part 1 (RealityOS Thesis) in current logs.")
    if not part2:
        print("Warning: Could not find Part 2 (Reviewer Research Plan) in current logs.")
        
    # Compile README
    if part1 or part2:
        combined = ""
        if part1:
            combined += part1 + "\n\n---\n\n"
        if part2:
            combined += part2
            
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(combined)
        print(f"README.md successfully updated at {readme_path}")
    else:
        print("Error: Could not extract either part.")
        
    # 2. Search both logs for Relational Engine code blocks
    print("Searching logs for Relational Engine code blocks...")
    found_code = []
    
    for path in [prev_log_path, curr_log_path]:
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                if any(kw in line for kw in ["RelationalEngine", "Relational_Engine", "Relational-Engine", "R-Identity", "R_Identity"]):
                    try:
                        data = json.loads(line)
                        content = data.get("content", "")
                        # Find python code blocks
                        code_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)
                        for cb in code_blocks:
                            code_text = cb.strip()
                            if code_text not in found_code:
                                found_code.append(code_text)
                    except:
                        continue
                        
    if found_code:
        print(f"Found {len(found_code)} distinct code blocks. Writing to {results_path}...")
        with open(results_path, 'w', encoding='utf-8') as f:
            for idx, cb in enumerate(found_code, 1):
                f.write(f"# === CODE BLOCK {idx} ===\n")
                f.write(cb)
                f.write("\n\n")
        print("Success! Extracted code blocks written.")
    else:
        print("No code blocks found in log files.")

if __name__ == "__main__":
    main()
