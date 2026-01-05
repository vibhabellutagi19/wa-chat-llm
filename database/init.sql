-- Initialize WhatsApp Bot Database Schema
-- This script runs automatically when the container first starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255),
    phone_number VARCHAR(20) UNIQUE NOT NULL,  -- E.164 format: +1234567890 (max 15 digits + prefix)
    full_name VARCHAR(255),
    hashed_password VARCHAR(255),
    password_history JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create userchats table
CREATE TABLE IF NOT EXISTS userchats (
    chat_id VARCHAR(50) PRIMARY KEY,
    customer_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT true,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_userchats_customer_id ON userchats(customer_id);
CREATE INDEX IF NOT EXISTS idx_userchats_is_active ON userchats(is_active);
CREATE INDEX IF NOT EXISTS idx_userchats_created_at ON userchats(created_at DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_userchats_updated_at
    BEFORE UPDATE ON userchats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional - remove in production)
-- INSERT INTO users (phone_number, full_name)
-- VALUES ('+1234567890', 'Test User');

COMMENT ON TABLE users IS 'Stores user information from WhatsApp';
COMMENT ON TABLE userchats IS 'Stores chat sessions with message history in JSONB format';
COMMENT ON COLUMN users.phone_number IS 'Phone number in E.164 format without whatsapp: prefix (e.g., +1234567890)';
COMMENT ON COLUMN userchats.messages IS 'JSONB array of message objects with role, content, and timestamp';
