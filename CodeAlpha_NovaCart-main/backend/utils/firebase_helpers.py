import os
import json
import uuid
import datetime
from pathlib import Path
from django.conf import settings

# Try to import firebase_admin, if not available or mocked, fallback gracefully
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    FIREBASE_INSTALLED = True
except ImportError:
    FIREBASE_INSTALLED = False

# Path to the mock database JSON
MOCK_DB_PATH = settings.BASE_DIR / 'db_mock.json'

class MockDocument:
    def __init__(self, id, data):
        self.id = id
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data

class MockDocumentReference:
    def __init__(self, collection_name, doc_id, mock_db):
        self.collection_name = collection_name
        self.id = doc_id
        self.mock_db = mock_db

    def get(self):
        data = self.mock_db._read_db().get(self.collection_name, {}).get(self.id)
        return MockDocument(self.id, data)

    def set(self, data, merge=False):
        db = self.mock_db._read_db()
        if self.collection_name not in db:
            db[self.collection_name] = {}
        
        # Serialize datetime objects to ISO strings
        serialized_data = self._serialize(data)
        
        if merge and self.id in db[self.collection_name]:
            db[self.collection_name][self.id].update(serialized_data)
        else:
            db[self.collection_name][self.id] = serialized_data
        
        self.mock_db._write_db(db)

    def update(self, data):
        db = self.mock_db._read_db()
        if self.collection_name in db and self.id in db[self.collection_name]:
            serialized_data = self._serialize(data)
            db[self.collection_name][self.id].update(serialized_data)
            self.mock_db._write_db(db)
        else:
            raise Exception(f"Document {self.id} does not exist in collection {self.collection_name}")

    def delete(self):
        db = self.mock_db._read_db()
        if self.collection_name in db and self.id in db[self.collection_name]:
            del db[self.collection_name][self.id]
            self.mock_db._write_db(db)

    def _serialize(self, val):
        if isinstance(val, dict):
            return {k: self._serialize(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [self._serialize(v) for v in val]
        elif isinstance(val, (datetime.datetime, datetime.date)):
            return val.isoformat()
        return val

class MockCollectionReference:
    def __init__(self, name, mock_db):
        self.name = name
        self.mock_db = mock_db

    def document(self, doc_id):
        return MockDocumentReference(self.name, doc_id, self.mock_db)

    def add(self, data):
        db = self.mock_db._read_db()
        if self.name not in db:
            db[self.name] = {}
        doc_id = str(uuid.uuid4())
        ref = self.document(doc_id)
        ref.set(data)
        return doc_id, ref

    def stream(self):
        db = self.mock_db._read_db()
        collection = db.get(self.name, {})
        return [MockDocument(k, v) for k, v in collection.items()]

    def get(self):
        return self.stream()

class MockFirestoreClient:
    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.exists(filepath):
            self._write_db({})

    def _read_db(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_db(self, db):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, default=str)

    def collection(self, name):
        return MockCollectionReference(name, self)

# Global variables for firebase connection
_db_client = None
_firebase_app = None

def get_firestore_client():
    global _db_client, _firebase_app
    
    # Check if mock mode is requested or firebase SDK is not available
    if settings.FIREBASE_MOCK_MODE or not FIREBASE_INSTALLED:
        if not _db_client or not isinstance(_db_client, MockFirestoreClient):
            _db_client = MockFirestoreClient(MOCK_DB_PATH)
        return _db_client
    
    # Real Firestore setup
    if not _db_client:
        try:
            if not firebase_admin._apps:
                cred_path = settings.FIREBASE_SERVICE_ACCOUNT_PATH
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    _firebase_app = firebase_admin.initialize_app(cred)
                else:
                    # Initialize default app if standard environment auth is available
                    _firebase_app = firebase_admin.initialize_app()
            _db_client = firestore.client()
        except Exception as e:
            # Fallback to mock if real configuration fails
            print(f"Error initializing Firebase. Falling back to mock database: {e}")
            _db_client = MockFirestoreClient(MOCK_DB_PATH)
            
    return _db_client

def verify_firebase_token(id_token):
    """
    Verifies the ID token sent from the client.
    If running in Mock Mode, supports mock tokens formatted as 'mock-token-[uid]-[email]-[role]'
    """
    if not id_token:
        return None

    if settings.FIREBASE_MOCK_MODE or not FIREBASE_INSTALLED:
        if id_token.startswith("mock-token-"):
            parts = id_token.split("-")
            # format: mock-token-[uid]-[email]-[role]
            uid = parts[2] if len(parts) > 2 else "mock_uid"
            email = parts[3] if len(parts) > 3 else "mock_user@novacart.com"
            role = parts[4] if len(parts) > 4 else "user"
            return {
                "uid": uid,
                "email": email,
                "name": email.split("@")[0].capitalize(),
                "role": role,
                "firebase": {"sign_in_provider": "custom"}
            }
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        # Check custom claims or fetch user record to inject role
        uid = decoded_token['uid']
        # Try to read custom role from Firestore users collection
        db = get_firestore_client()
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            decoded_token['role'] = user_doc.to_dict().get('role', 'user')
        else:
            decoded_token['role'] = 'user'
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None
