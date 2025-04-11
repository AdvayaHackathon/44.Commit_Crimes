import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import getpass

# No environment variables needed for this script

# Get database connection parameters
def get_db_params():
    print("PostgreSQL Database Setup")
    print("--------------------------")
    host = input("Enter database host (default: localhost): ") or "localhost"
    user = input("Enter database username (default: postgres): ") or "postgres"
    password = getpass.getpass("Enter database password: ")
    db_name = input("Enter database name (default: user_dashboard): ") or "user_dashboard"

    return {
        'host': host,
        'user': user,
        'password': password,
        'db_name': db_name
    }

def create_database(db_params):
    """Create the database for the application"""
    db_name = db_params.pop('db_name')  # Remove db_name from connection params

    try:
        # Connect to PostgreSQL server
        print("\nConnecting to PostgreSQL server...")
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()

        if not exists:
            print(f"Creating database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print("Database created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")

        cursor.close()
        conn.close()

        # Connect to the newly created database
        db_params['database'] = db_name
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Try to enable pgvector extension if available
        try:
            print("Checking for pgvector extension...")
            cursor.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector'")
            pgvector_available = cursor.fetchone()

            if pgvector_available:
                print("Enabling pgvector extension...")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                print("pgvector extension enabled successfully!")
            else:
                print("pgvector extension is not available. Skipping...")
                print("The application will work without vector search capabilities.")
        except Exception as e:
            print(f"Could not enable pgvector extension: {e}")
            print("This is OK - the application will work without vector search capabilities.")

        cursor.close()
        conn.close()

        print("\n✅ Database setup completed successfully!")
        print(f"Database '{db_name}' is ready to use.")
        print("\nYou can now run 'python app.py' to start the application.")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check your PostgreSQL installation and credentials.")
        return False

if __name__ == "__main__":
    db_params = get_db_params()
    create_database(db_params)
