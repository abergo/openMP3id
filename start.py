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
        p = Path(path_str)
        if p.exists() and p.is_dir():
            return str(p.absolute())
        elif create_if_missing:
            print(f"Directory doesn't exist. Creating {p.absolute()}...")
            p.mkdir(parents=True, exist_ok=True)
            return str(p.absolute())
        else:
            print("  [!] Error: That path does not exist. Please enter a valid directory.")

def run_docker():
    clear_screen()
    print("=== DOCKER MODE ===")
    input_path = validate_path("\nPlease paste the absolute path to your RAW music folder:\n> ", create_if_missing=False)
    output_path = validate_path("\nPlease paste the absolute path to save your ORGANIZED library:\n> ", create_if_missing=True)
    
    print("\n  [~] Building Docker Image (this is fast if already built)...")
    build_code = os.system("docker build -t openmp3id .")
    if build_code != 0:
        print("  [!] Error: Docker failed to build. Is Docker Desktop running?")
        sys.exit(1)
        
    print(f"\n  [~] Running openMP3id securely via Docker container...")
    print(f"      Mapping Input : {input_path}")
    print(f"      Mapping Output: {output_path}\n")
    
    run_cmd = f'docker run --rm -v "{input_path}:/input_music" -v "{output_path}:/organized_library" openmp3id'
    os.system(run_cmd)

def run_native():
    clear_screen()
    print("=== NATIVE VENV MODE ===")
    print("Warning: This requires FFmpeg to be installed on your host system to process non-MP3 files natively.")
    input("Press Enter to continue or Ctrl+C to abort...")
    
    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print("\n  [~] Creating isolated Python Virtual Environment...")
        venv.create(venv_dir, with_pip=True)
        
    # Determine execution paths for windows vs posix
    if os.name == 'nt':
        pip_exe = str(venv_dir / "Scripts" / "pip.exe")
        python_exe = str(venv_dir / "Scripts" / "python.exe")
    else:
        pip_exe = str(venv_dir / "bin" / "pip")
        python_exe = str(venv_dir / "bin" / "python")
        
    print("\n  [~] Verifying dependencies inside Virtual Environment...")
    subprocess.check_call([pip_exe, "install", "--no-cache-dir", "-r", "requirements.txt"])
    
    input_path = validate_path("\nPlease paste the absolute path to your RAW music folder:\n> ", create_if_missing=False)
    output_path = validate_path("\nPlease paste the absolute path to save your ORGANIZED library:\n> ", create_if_missing=True)
    
    print("\n  [~] Booting Native openMP3id agent...\n")
    subprocess.check_call([python_exe, "organizer.py", "-i", input_path, "-o", output_path])

def main():
    clear_screen()
    print("Welcome to openMP3id - The Automated Music Librarian")
    print("="*50)
    print("Select your launch configuration:")
    print("  [1] \U0001F433 Docker Secure Container (Highly Recommended)")
    print("  [2] \U0001F40D Native Python Virtual Environment")
    print("  [3] Exit")
    
    while True:
        choice = input("\nEnter choice (1/2/3): ").strip()
        if choice == '1':
            run_docker()
            break
        elif choice == '2':
            run_native()
            break
        elif choice == '3':
            sys.exit(0)
        else:
            print("Invalid selection.")

if __name__ == "__main__":
    main()
