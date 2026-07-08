import json
import os
import re

def main():
    prev_log_path = r"C:\Users\namir\.gemini\antigravity-ide\brain\66c52d3e-6829-409a-a948-538c4aa70d32\.system_generated\logs\transcript_full.jsonl"
    curr_log_path = r"C:\Users\namir\.gemini\antigravity-ide\brain\9d3b5cfa-efc2-400d-84e6-addfd053ebcf\.system_generated\logs\transcript_full.jsonl"
    out_path = r"c:\Users\namir\OneDrive\Desktop\project S\search_results.txt"
    
    results = []
    
    paths = [prev_log_path, curr_log_path]
    for path in paths:
        if not os.path.exists(path):
            results.append(f"File not found: {path}\n")
            continue
            
        results.append(f"=== Searching in {path} ===\n")
        with open(path, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                # Search for keywords
                if any(kw in line for kw in ["R-Identity", "Relational-Engine", "RelationalEngine", "Relational_Engine", "identity over 10"]):
                    results.append(f"Line {idx}: keyword found.\n")
                    try:
                        data = json.loads(line)
                        content = data.get("content", "")
                        # Try to find code blocks in content
                        code_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)
                        if code_blocks:
                            for cb_idx, cb in enumerate(code_blocks, 1):
                                results.append(f"Code block {cb_idx}:\n{cb.strip()}\n\n")
                        else:
                            # Just write the text around the match
                            results.append(f"Content excerpt:\n{content[:2000]}...\n\n")
                    except Exception as e:
                        results.append(f"Error parsing JSON on line {idx}: {e}\n")
                        
    with open(out_path, 'w', encoding='utf-8') as f:
        f.writelines(results)
    print(f"Results written to {out_path}")

if __name__ == "__main__":
    main()
