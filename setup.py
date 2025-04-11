import subprocess
import sys
import os

def setup_project():
    """Set up the project by creating a virtual environment and installing dependencies"""
    print("Project Setup")
    print("------------")
    
    # Check if Python is installed
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    
    # Check if virtual environment exists
    venv_exists = os.path.exists("venv")
    
    if not venv_exists:
        print("\nCreating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("Virtual environment created successfully!")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}")
            return
    else:
        print("\nVirtual environment already exists.")
    
    # Determine the path to the virtual environment's Python executable
    if os.name == 'nt':  # Windows
        venv_python = os.path.join("venv", "Scripts", "python.exe")
        venv_pip = os.path.join("venv", "Scripts", "pip.exe")
    else:  # macOS/Linux
        venv_python = os.path.join("venv", "bin", "python")
        venv_pip = os.path.join("venv", "bin", "pip")
    
    # Install dependencies
    print("\nInstalling dependencies...")
    try:
        subprocess.run([venv_pip, "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return
    
    print("\nProject setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # macOS/Linux
        print("   source venv/bin/activate")
    print("2. Check if pgvector is available:")
    print("   python check_pgvector.py")
    print("3. Set up environment variables:")
    print("   python setup_env.py")
    print("4. Initialize the database:")
    print("   python init_db.py")
    print("5. Run the application:")
    print("   python app.py")

if __name__ == "__main__":
    setup_project()
