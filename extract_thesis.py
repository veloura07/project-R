import json
import os

def main():
    log_path = r"C:\Users\namir\.gemini\antigravity-ide\brain\9d3b5cfa-efc2-400d-84e6-addfd053ebcf\.system_generated\logs\transcript_full.jsonl"
    dest_path = r"c:\Users\namir\OneDrive\Desktop\project S\README.md"
    
    if not os.path.exists(log_path):
        print(f"Error: Log file not found at {log_path}")
        return
        
    print(f"Reading logs from {log_path}...")
    
    thesis_content = None
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                content = data.get("content", "")
                if "RealityOS — An Event-Driven" in content:
                    # Found the thesis!
                    thesis_content = content
                    # Remove the <USER_REQUEST> and </USER_REQUEST> tags if present
                    if thesis_content.startswith("<USER_REQUEST>\n"):
                        thesis_content = thesis_content[len("<USER_REQUEST>\n"):]
                    if thesis_content.endswith("\n</USER_REQUEST>"):
                        thesis_content = thesis_content[:-len("\n</USER_REQUEST>")]
                    break
            except Exception as e:
                continue
                
    if not thesis_content:
        print("Error: Could not find the thesis document in the logs.")
        return
        
    print(f"Found thesis (length {len(thesis_content)} chars). Writing to {dest_path}...")
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(thesis_content)
    print("Success! README.md has been updated with the RealityOS thesis.")

if __name__ == "__main__":
    main()
