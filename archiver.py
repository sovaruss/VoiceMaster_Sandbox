import zipfile
import os

def create_zip(original, translated, filename):
    base = os.path.splitext(filename)[0] if filename else "VoiceMaster"
    zip_path = f"{base}_report.zip"
    txt_path = f"{base}_translation.txt"
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"--- ORIGINAL ---\n{original}\n\n--- TRANSLATION ---\n{translated}")
    
    with zipfile.ZipFile(zip_path, 'w') as z:
        z.write(txt_path)
    
    if os.path.exists(txt_path): os.remove(txt_path)
    return zip_path