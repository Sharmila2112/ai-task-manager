from dotenv import load_dotenv
from app import create_app, db

# Load environment variables
load_dotenv()

app = create_app()

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)