import webbrowser
import sys
import os
import platform

def install_postgres():
    """Guide the user through PostgreSQL installation"""
    print("PostgreSQL Installation Guide")
    print("----------------------------")
    
    # Detect operating system
    os_name = platform.system()
    print(f"Detected operating system: {os_name}")
    
    if os_name == "Windows":
        print("\nTo install PostgreSQL on Windows:")
        print("1. Download the installer from the official website")
        print("2. Run the installer and follow the instructions")
        print("3. Remember the password you set for the 'postgres' user")
        print("4. After installation, run 'python check_pgvector.py' to verify the connection")
        
        # Ask if user wants to open the download page
        open_browser = input("\nWould you like to open the PostgreSQL download page? (y/n): ").lower()
        if open_browser == 'y':
            webbrowser.open("https://www.postgresql.org/download/windows/")
            print("\nDownload page opened in your browser.")
            print("After downloading, run the installer and follow the instructions.")
    
    elif os_name == "Darwin":  # macOS
        print("\nTo install PostgreSQL on macOS:")
        print("1. Using Homebrew (recommended):")
        print("   brew install postgresql")
        print("   brew services start postgresql")
        print("\n2. Or download the installer from the official website")
        
        # Ask if user wants to open the download page
        open_browser = input("\nWould you like to open the PostgreSQL download page? (y/n): ").lower()
        if open_browser == 'y':
            webbrowser.open("https://www.postgresql.org/download/macosx/")
            print("\nDownload page opened in your browser.")
    
    elif os_name == "Linux":
        print("\nTo install PostgreSQL on Linux:")
        print("For Ubuntu/Debian:")
        print("   sudo apt update")
        print("   sudo apt install postgresql postgresql-contrib")
        print("   sudo systemctl start postgresql")
        print("   sudo systemctl enable postgresql")
        print("\nFor Red Hat/Fedora/CentOS:")
        print("   sudo dnf install postgresql-server postgresql-contrib")
        print("   sudo postgresql-setup --initdb")
        print("   sudo systemctl start postgresql")
        print("   sudo systemctl enable postgresql")
    
    else:
        print("\nUnsupported operating system. Please visit the PostgreSQL website for installation instructions:")
        print("https://www.postgresql.org/download/")
    
    print("\nAfter installing PostgreSQL:")
    print("1. Run 'python check_pgvector.py' to verify the connection")
    print("2. Run 'python setup_env.py' to set up environment variables")
    print("3. Run 'python init_db.py' to create the database")
    print("4. Run 'python app.py' to start the application")

if __name__ == "__main__":
    install_postgres()
