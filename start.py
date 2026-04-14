import os
import sys
import subprocess
from pathlib import Path
import venv

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def validate_path(prompt_text, create_if_missing=False):
    while True:
        path_str = input(prompt_text).strip().strip('"').strip("'")
        if not path_str:
            print("  [!] Error: Path cannot be empty.")
            continue
        p = Path(path_str)
        if p.exists() and p.is_dir():
            return str(p.absolute())
        elif create_if_missing:
            print(f"Directory doesn't exist. Creating {p.absolute()}...")
            p.mkdir(parents=True, exist_ok=True)
            return str(p.absolute())
        else:
            print("  [!] Error: That path does not exist. Please enter a valid directory.")

def load_env():
    env_vars = {}
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        k, v = line.split('=', 1)
                        env_vars[k.strip()] = v.strip().strip("'").strip('"')
    return env_vars

def save_env(env_vars):
    with open(".env", "w", encoding="utf-8") as f:
        for k, v in env_vars.items():
            f.write(f'{k}="{v}"\n')

def get_python_exe():
    venv_dir = Path(".venv")
    if os.name == 'nt':
        return str(venv_dir / "Scripts" / "python.exe") if venv_dir.exists() else "python"
    else:
        return str(venv_dir / "bin" / "python") if venv_dir.exists() else "python3"

def run_docker(input_path, output_path):
    clear_screen()
    print("=== DOCKER MODE ===")
    print("\n  [~] Building Docker Image (this is fast if already built)...")
    build_code = os.system("docker build -t openmp3id .")
    if build_code != 0:
        print("  [!] Error: Docker failed to build. Is Docker Desktop running?")
        input("Press Enter to return to menu...")
        return
        
    print(f"\n  [~] Running openMP3id securely via Docker container...")
    print(f"      Mapping Input : {input_path}")
    print(f"      Mapping Output: {output_path}\n")
    
    run_cmd = f'docker run --rm -v "{input_path}:/input_music" -v "{output_path}:/organized_library" openmp3id'
    os.system(run_cmd)
    input("\nPress Enter to return to main menu...")

def run_native(input_path, output_path):
    clear_screen()
    print("=== NATIVE VENV MODE ===")
    print("Warning: This requires FFmpeg to be installed on your host system to process non-MP3 files natively.")
    input("\nPress Enter to continue or Ctrl+C to abort...")
    
    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print("\n  [~] Creating isolated Python Virtual Environment...")
        venv.create(venv_dir, with_pip=True)
        
    if os.name == 'nt':
        pip_exe = str(venv_dir / "Scripts" / "pip.exe")
        python_exe = str(venv_dir / "Scripts" / "python.exe")
    else:
        pip_exe = str(venv_dir / "bin" / "pip")
        python_exe = str(venv_dir / "bin" / "python")
        
    print("\n  [~] Verifying dependencies inside Virtual Environment...")
    subprocess.check_call([pip_exe, "install", "--no-cache-dir", "-r", "requirements.txt"])
    
    print("\n  [~] Booting Native openMP3id agent...\n")
    try:
        subprocess.check_call([python_exe, "organizer.py", "-i", input_path, "-o", output_path])
    except subprocess.CalledProcessError:
        print("\n  [!] Agent exited with an error.")
    input("\nPress Enter to return to main menu...")

def configure_paths(env_vars):
    clear_screen()
    print("=== CONFIGURE PATHS ===")
    print("Current Input :", env_vars.get("INPUT_FOLDER", "Not Set"))
    print("Current Output:", env_vars.get("OUTPUT_FOLDER", "Not Set"))
    
    print("\n[Press Enter without typing to keep current value]")
    
    new_input = input("\nEnter absolute path for RAW music folder:\n> ").strip().strip('"').strip("'")
    if new_input:
        if Path(new_input).exists() and Path(new_input).is_dir():
            env_vars["INPUT_FOLDER"] = str(Path(new_input).absolute())
        else:
            print("  [!] Error: Provided path is not a valid directory. Keeping previous input.")
            
    new_output = input("\nEnter absolute path for ORGANIZED library (Output):\n> ").strip().strip('"').strip("'")
    if new_output:
        p = Path(new_output)
        if not p.exists():
            print(f"Directory doesn't exist. Creating {p.absolute()}...")
            p.mkdir(parents=True, exist_ok=True)
        env_vars["OUTPUT_FOLDER"] = str(p.absolute())
        
    save_env(env_vars)
    print("\n  [+] Settings updated.")
    input("Press Enter to continue...")
    return env_vars

def prompt_missing_paths(env_vars):
    updated = False
    if "INPUT_FOLDER" not in env_vars or not Path(env_vars["INPUT_FOLDER"]).exists():
        print("\n[!] Input folder missing or invalid.")
        input_val = validate_path("Please paste the absolute path to your RAW music folder:\n> ", create_if_missing=False)
        env_vars["INPUT_FOLDER"] = input_val
        updated = True
        
    if "OUTPUT_FOLDER" not in env_vars:
        print("\n[!] Output folder missing or invalid.")
        output_val = validate_path("Please paste the absolute path to save your ORGANIZED library:\n> ", create_if_missing=True)
        env_vars["OUTPUT_FOLDER"] = output_val
        updated = True

    if updated:
        save_env(env_vars)
    return env_vars

def main():
    while True:
        clear_screen()
        env_vars = load_env()
        input_dir = env_vars.get("INPUT_FOLDER", "Not Set")
        output_dir = env_vars.get("OUTPUT_FOLDER", "Not Set")

        db_path = None
        db_exists = False
        if output_dir != "Not Set" and Path(output_dir).exists():
            db_path = Path(output_dir) / "openmp3id.db"
            db_exists = db_path.exists()

        print("Welcome to openMP3id - The Automated Music Librarian")
        print("="*50)
        print("Current Configuration:")
        print(f"  [Input]  RAW folder : {input_dir}")
        print(f"  [Output] ORG library: {output_dir}")
        print(f"  [DB]     Status     : {'Exists (Ready)' if db_exists else 'Not Found (Will create on run)'}")
        print("="*50)

        print("Select an action:")
        print("  [1] \U0001F433 START openMP3id (Docker - Default/Recommended)")
        print("  [2] \U0001F40D START openMP3id (Native Python venv)")
        print("  [3] \u2699\uFE0F  Configure Paths")
        if db_exists:
            print("  [4] \U0001F5D1\uFE0F  Delete/Reset Database")
            print("  [5] \U0001F50E Scan Output Directory (Update DB)")
        print("  [0] Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            env_vars = prompt_missing_paths(env_vars)
            run_docker(env_vars["INPUT_FOLDER"], env_vars["OUTPUT_FOLDER"])
        elif choice == '2':
            env_vars = prompt_missing_paths(env_vars)
            run_native(env_vars["INPUT_FOLDER"], env_vars["OUTPUT_FOLDER"])
        elif choice == '3':
            env_vars = configure_paths(env_vars)
        elif choice == '4' and db_exists:
            confirm = input(f"\nAre you sure you want to delete '{db_path}'? (y/N): ").strip().lower()
            if confirm == 'y':
                python_exe = get_python_exe()
                subprocess.check_call([python_exe, "manage_db.py", "--db", str(db_path), "--reset"])
                input("\nPress Enter to continue...")
        elif choice == '5' and db_exists:
            scan_dir = validate_path(f"\nEnter the absolute directory to scan (default {output_dir}):\n> ", create_if_missing=False)
            python_exe = get_python_exe()
            subprocess.check_call([python_exe, "manage_db.py", "--db", str(db_path), "--scan", scan_dir])
            input("\nPress Enter to continue...")
        elif choice == '0':
            sys.exit(0)
        else:
            print("\nInvalid selection.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main()
