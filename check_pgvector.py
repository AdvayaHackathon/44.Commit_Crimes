import psycopg2
import getpass

def check_postgres_connection():
    """Check PostgreSQL connection and pgvector availability"""
    print("PostgreSQL Connection Check")
    print("--------------------------")

    # Get database connection parameters
    host = input("Enter database host (default: localhost): ") or "localhost"
    user = input("Enter database username (default: postgres): ") or "postgres"
    password = getpass.getpass("Enter database password: ")

    try:
        # Connect to PostgreSQL server
        print("\nConnecting to PostgreSQL server...")
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname="postgres"  # Connect to default database
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("\n✅ Successfully connected to PostgreSQL server!")

        # Check PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"\nPostgreSQL version: {version}")

        # Check if pgvector is available
        try:
            cursor.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector'")
            result = cursor.fetchone()

            if result:
                print("\n✅ pgvector extension is available in your PostgreSQL installation.")
                print(f"   Extension details: {result}")
            else:
                print("\n⚠️ pgvector extension is NOT available in your PostgreSQL installation.")
                print("   This is OK - the application will work without vector search capabilities.")
                print("\n   If you want to enable vector search later:")
                print("   1. Install the pgvector extension for PostgreSQL")
                print("   2. Follow instructions at: https://github.com/pgvector/pgvector")
        except Exception as e:
            print(f"\n⚠️ Could not check for pgvector extension: {e}")
            print("   This is OK - the application will work without vector search capabilities.")

        print("\n✅ Your PostgreSQL connection is working correctly!")
        print("\nYou can now run 'python setup_env.py' to set up your environment variables.")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check your PostgreSQL installation and credentials.")
        print("\nCommon issues:")
        print("1. PostgreSQL service is not running")
        print("2. Incorrect username or password")
        print("3. PostgreSQL is not installed")
        print("\nTo install PostgreSQL on Windows:")
        print("1. Download the installer from https://www.postgresql.org/download/windows/")
        print("2. Run the installer and follow the instructions")
        print("3. Remember the password you set for the 'postgres' user")
        print("4. After installation, run this script again")
        return False

if __name__ == "__main__":
    check_postgres_connection()
