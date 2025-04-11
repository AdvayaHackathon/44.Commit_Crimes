from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

# Import langchain libraries
try:
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain_ollama import OllamaEmbeddings, OllamaLLM
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_community.document_loaders import PDFPlumberLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Load environment variables
load_dotenv()

# Get database connection parameters
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', 'user_dashboard')

# Construct database URL
db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-testing')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', db_url)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize vector store and document chunks
vector_store = None
document_chunks = []
if LANGCHAIN_AVAILABLE:
    try:
        vector_store = InMemoryVectorStore(OllamaEmbeddings(model="deepseek-r1:1.5b"))
    except Exception as e:
        print(f"Error initializing vector store: {e}")

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if username or email already exists
        user_exists = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()

        if user_exists:
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))

        if email_exists:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/coach')
@login_required
def coach():
    return render_template('coach.html')

@app.route('/content')
@login_required
def content():
    return render_template('content.html')

@app.route('/planner')
@login_required
def planner():
    return render_template('planner.html')

@app.route('/test')
@login_required
def test():
    return render_template('test.html')

@app.route('/feedback')
@login_required
def feedback():
    return render_template('feedback.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/learning_path')
@login_required
def learning_path():
    if not LANGCHAIN_AVAILABLE:
        flash('The required libraries for Learning Path are not installed. Please install langchain and related packages.', 'error')
        return redirect(url_for('dashboard'))

    # Initialize chat messages if not exists
    if 'chat_messages' not in session:
        session['chat_messages'] = []

    # Get list of processed files
    processed_files = session.get('processed_files', [])

    return render_template('learning_path.html', messages=session['chat_messages'], processed_files=processed_files)

@app.route('/learning_path/upload', methods=['POST'])
@login_required
def learning_path_upload():
    if not LANGCHAIN_AVAILABLE:
        return jsonify({'error': 'The required libraries for Learning Path are not installed.'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('file')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400

    total_files = len([f for f in files if f.filename.endswith('.pdf')])
    if total_files == 0:
        return jsonify({'error': 'No PDF files selected'}), 400

    processed_files = []
    skipped_files = []
    failed_files = []
    
    # Create necessary directories if they don't exist
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'document_store')
    upload_folder = os.path.join(base_dir, 'pdfs')
    os.makedirs(upload_folder, exist_ok=True)

    # Use global vector store
    global vector_store, document_chunks
    if vector_store is None:
        try:
            vector_store = InMemoryVectorStore(OllamaEmbeddings(model="deepseek-r1:1.5b"))
        except Exception as e:
            return jsonify({
                'error': f'Error initializing vector store: {str(e)}',
                'status': 'failed',
                'details': 'Vector store initialization failed'
            }), 500

    for file in files:
        if file and file.filename.endswith('.pdf'):
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)

                # Save file
                file.save(file_path)

                # Process document
                document_loader = PDFPlumberLoader(file_path)
                raw_docs = document_loader.load()

                # Split into chunks
                text_processor = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    add_start_index=True
                )
                chunks = text_processor.split_documents(raw_docs)

                if chunks:
                    # Add to vector store and document chunks
                    vector_store.add_documents(chunks)
                    document_chunks.extend(chunks)
                    
                    # Update processed files list in session
                    if 'processed_files' not in session:
                        session['processed_files'] = []
                    if filename not in session['processed_files']:
                        session['processed_files'].append(filename)
                        processed_files.append(filename)
                    
                    # Ensure changes are saved to session
                    session.modified = True
                else:
                    skipped_files.append({
                        'name': filename,
                        'reason': 'No content could be extracted'
                    })
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
            except Exception as e:
                # If file was saved but processing failed, try to clean up
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                failed_files.append({
                    'name': file.filename,
                    'error': str(e)
                })
        else:
            skipped_files.append({
                'name': file.filename,
                'reason': 'Not a PDF file'
            })

    # Prepare detailed response
    response = {
        'status': 'completed',
        'total_files': total_files,
        'processed': {
            'count': len(processed_files),
            'files': processed_files
        },
        'skipped': {
            'count': len(skipped_files),
            'files': skipped_files
        },
        'failed': {
            'count': len(failed_files),
            'files': failed_files
        },
        'total_documents_available': len(session.get('processed_files', [])),
        'total_chunks': len(document_chunks),
        'message': f'Processing completed. Successfully processed {len(processed_files)} files into {len(document_chunks)} chunks for analysis.'
    }

    if len(processed_files) > 0:
        return jsonify(response)
    else:
        response['status'] = 'failed'
        response['error'] = 'No files were successfully processed'
        return jsonify(response), 400

@app.route('/learning_path/chat', methods=['POST'])
@login_required
def learning_path_chat():
    if not LANGCHAIN_AVAILABLE:
        return jsonify({'error': 'The required libraries for Learning Path are not installed.'}), 400

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message']

    # Add user message to chat history
    if 'chat_messages' not in session:
        session['chat_messages'] = []
    session['chat_messages'].append({'role': 'user', 'content': user_message})

    # Check if any documents are processed
    if not session.get('processed_files', []):
        return jsonify({'error': 'Please upload some PDF documents first'}), 400

    # Generate response using global vector store
    global vector_store
    if vector_store is not None:
        try:
            # Initialize language model with better parameters
            language_model = OllamaLLM(
                model="deepseek-r1:1.5b",
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                num_ctx=4096
            )

            # Search for relevant documents with increased k for better context
            relevant_docs = vector_store.similarity_search(user_message, k=5)

            # Generate answer with improved prompt
            prompt_template = """
            You are a multilingual expert research assistant analyzing multiple documents. You MUST follow these rules:
            1. ALWAYS detect the language of the user's query
            2. If the query is in Kannada (ಕನ್ನಡ), you MUST respond in Kannada
            3. If the query is in Hindi (हिंदी), you MUST respond in Hindi
            4. If the query is in English, respond in English
            5. Analyze and combine information from ALL relevant documents
            6. Translate relevant context from English to the query language
            7. Be clear and informative in your response
            8. Cite which document(s) you're referencing
            9. If information conflicts between documents, point out the differences
            10. If unsure, ask for clarification in the same language

            User Query: {user_query}

            Available Documents: {doc_list}

            Relevant Context from Documents:
            {document_context}

            Remember to:
            - Respond in the SAME LANGUAGE as the query
            - Cite your sources
            - Be clear and thorough
            - Compare information across documents when relevant
            """

            # Prepare document list and context with better organization
            doc_list = ", ".join(session.get('processed_files', []))
            context_text = "\n\n".join([
                f"From {doc.metadata.get('source', 'document')} (Section {doc.metadata.get('start_index', 'unknown')}):\n{doc.page_content}"
                for doc in relevant_docs
            ])

            conversation_prompt = ChatPromptTemplate.from_template(prompt_template)
            response_chain = conversation_prompt | language_model
            ai_response = response_chain.invoke({
                "user_query": user_message,
                "document_context": context_text,
                "doc_list": doc_list
            })

            # Add AI response to chat history
            session['chat_messages'].append({'role': 'assistant', 'content': ai_response})
            session.modified = True

            return jsonify({
                'response': ai_response,
                'messages': session['chat_messages'],
                'context': {
                    'total_documents': len(session.get('processed_files', [])),
                    'chunks_searched': len(relevant_docs),
                    'documents_referenced': list(set(doc.metadata.get('source', 'unknown') for doc in relevant_docs))
                }
            })
        except Exception as e:
            return jsonify({'error': f'Error generating response: {str(e)}'}), 500

    return jsonify({
        'error': 'Please upload documents first'
    }), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
