"""Database Models and Configuration for Production LLM Routing System"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum
import os

Base = declarative_base()

# ==================== ENUMS ====================
class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    ENTERPRISE = "enterprise"

class APIKeySource(enum.Enum):
    SYSTEM_PROVIDED = "system_provided"  # System provides API Keys
    USER_PROVIDED = "user_provided"      # User enters their own API Keys

class FeedbackRating(enum.Enum):
    EXCELLENT = "excellent"      # Excellent
    GOOD = "good"                # Good
    AVERAGE = "average"          # Average
    POOR = "poor"                # Poor
    VERY_POOR = "very_poor"      # Very poor

# ==================== MODELS ====================
class User(Base):
    """User model - User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company = Column(String(255))
    
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    api_key_source = Column(SQLEnum(APIKeySource), default=APIKeySource.SYSTEM_PROVIDED)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Usage limits
    monthly_query_limit = Column(Integer, default=1000)
    queries_used_this_month = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    api_keys = relationship("UserAPIKey", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("QueryLog", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class UserAPIKey(Base):
    """User's own API Keys"""
    __tablename__ = "user_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    provider = Column(String(50), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    key_name = Column(String(100))
    model_name = Column(String(300), nullable=False)  # Full model name (mistralai/mistral-7b-instruct:free)
    model_path = Column(String(300))  # Full model path (optional)
    tier = Column(String(20), default="tier1")  # tier1, tier2, or tier3
    
    # Pricing per 1M tokens
    input_price = Column(Float, default=0.15)
    output_price = Column(Float, default=0.15)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
    user = relationship("User", back_populates="api_keys")


class QueryLog(Base):
    """Query logs"""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    query_text = Column(Text, nullable=False)
    response_text = Column(Text)
    
    classification = Column(String(10))
    model_tier = Column(String(20))
    used_model = Column(String(100))
    
    cache_hit = Column(Boolean, default=False)
    processing_time = Column(Float)
    estimated_cost = Column(Float, default=0.0)
    
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    query_metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="queries")
    feedback = relationship("Feedback", back_populates="query", uselist=False)


class Feedback(Base):
    """User feedback"""
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query_id = Column(Integer, ForeignKey("query_logs.id"), nullable=False)
    
    rating = Column(SQLEnum(FeedbackRating), nullable=False)
    comment = Column(Text)
    
    classification_correct = Column(Boolean)
    model_appropriate = Column(Boolean)
    
    response_helpful = Column(Boolean)
    response_accurate = Column(Boolean)
    response_fast_enough = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="feedbacks")
    query = relationship("QueryLog", back_populates="feedback")


class PromptSuggestion(Base):
    """Prompt suggestions"""
    __tablename__ = "prompt_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    original_prompt = Column(Text, nullable=False)
    suggested_prompts = Column(JSON)
    
    user_id = Column(Integer, ForeignKey("users.id"))
    accepted = Column(Boolean)
    selected_suggestion = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    """Chat conversations - Chat conversations"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String(500), nullable=False)
    cache_file = Column(String(255))  # Path to semantic cache file for conversation
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Chat messages - Chat messages"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    query_id = Column(Integer, ForeignKey("query_logs.id"))  # Link with QueryLog
    
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Metadata for assistant messages (name changed from metadata because it's reserved)
    message_metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class SystemAPIKey(Base):
    """System API Keys"""
    __tablename__ = "system_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    key_name = Column(String(100))
    
    total_queries = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)


class ModelRating(Base):
    """Model Rating System - Model Rating System"""
    __tablename__ = "model_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    model_identifier = Column(String(300), unique=True, nullable=False, index=True)  # e.g., "qwen/qwen-2.5-72b-instruct:free"
    model_name = Column(String(200))  # Display name
    tier = Column(String(20), nullable=False)  # tier1, tier2, tier3
    
    # Rating scores
    score = Column(Integer, default=100)  # Current points
    total_likes = Column(Integer, default=0)
    total_dislikes = Column(Integer, default=0)
    total_stars = Column(Integer, default=0)
    total_feedbacks = Column(Integer, default=0)
    
    # Usage stats
    total_uses = Column(Integer, default=0)
    successful_uses = Column(Integer, default=0)
    failed_uses = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time = Column(Float, default=0.0)
    avg_cost = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime)


class ModelFeedback(Base):
    """Individual feedback on model responses - Individual feedback on model responses"""
    __tablename__ = "model_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("query_logs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_identifier = Column(String(300), nullable=False)
    
    # Feedback type: 'like', 'dislike', 'star'
    feedback_type = Column(String(20), nullable=False)
    points_change = Column(Integer, nullable=False)  # +5, -5, +10
    
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== DATABASE SETUP ====================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./llm_router.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Apply migrations for new columns
    migrate_user_api_keys()
    migrate_messages()
    
    # Initialize model ratings from config
    initialize_model_ratings()
    
    print("✅ Database initialized successfully!")


def initialize_model_ratings():
    """Initialize model ratings for all models in config"""
    from config import MODELS_CONFIG
    
    db = SessionLocal()
    try:
        for tier, models in MODELS_CONFIG.items():
            for model in models:
                if isinstance(model, (list, tuple)) and len(model) >= 2:
                    model_name = model[0]
                    model_identifier = model[1]
                else:
                    model_name = model
                    model_identifier = model
                
                # Check if model already exists
                existing = db.query(ModelRating).filter(
                    ModelRating.model_identifier == model_identifier
                ).first()
                
                if not existing:
                    new_rating = ModelRating(
                        model_identifier=model_identifier,
                        model_name=model_name,
                        tier=tier,
                        score=100
                    )
                    db.add(new_rating)
        
        db.commit()
        print("✅ Model ratings initialized")
    except Exception as e:
        print(f"⚠️  Error initializing model ratings: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_user_api_keys():
    """Add new columns to user_api_keys table if they don't exist"""
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    
    # Check if user_api_keys table exists
    if 'user_api_keys' not in inspector.get_table_names():
        return
    
    existing_columns = [col['name'] for col in inspector.get_columns('user_api_keys')]
    
    with engine.connect() as conn:
        # Add model_name column if it doesn't exist
        if 'model_name' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN model_name VARCHAR(200)"))
                conn.commit()
                print("✅ Added 'model_name' column to user_api_keys")
            except Exception as e:
                print(f"⚠️  model_name column might already exist: {e}")
        
        # Add model_path column if it doesn't exist
        if 'model_path' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN model_path VARCHAR(300)"))
                conn.commit()
                print("✅ Added 'model_path' column to user_api_keys")
            except Exception as e:
                print(f"⚠️  model_path column might already exist: {e}")
        
        # Add tier column if it doesn't exist
        if 'tier' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN tier VARCHAR(20) DEFAULT 'tier1'"))
                conn.commit()
                print("✅ Added 'tier' column to user_api_keys")
            except Exception as e:
                print(f"⚠️  tier column might already exist: {e}")
        
        # Add input_price column if it doesn't exist
        if 'input_price' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN input_price FLOAT DEFAULT 0.0"))
                conn.commit()
                print("✅ Added 'input_price' column to user_api_keys")
            except Exception as e:
                print(f"⚠️  input_price column might already exist: {e}")
        
        # Add output_price column if it doesn't exist
        if 'output_price' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE user_api_keys ADD COLUMN output_price FLOAT DEFAULT 0.0"))
                conn.commit()
                print("✅ Added 'output_price' column to user_api_keys")
            except Exception as e:
                print(f"⚠️  output_price column might already exist: {e}")


def migrate_messages():
    """Add query_id column to messages table if it doesn't exist"""
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    
    # Check if messages table exists
    if 'messages' not in inspector.get_table_names():
        return
    
    existing_columns = [col['name'] for col in inspector.get_columns('messages')]
    
    with engine.connect() as conn:
        # Add query_id column if it doesn't exist
        if 'query_id' not in existing_columns:
            try:
                conn.execute(text("ALTER TABLE messages ADD COLUMN query_id INTEGER"))
                conn.commit()
                print("✅ Added 'query_id' column to messages")
            except Exception as e:
                print(f"⚠️  query_id column might already exist: {e}")
