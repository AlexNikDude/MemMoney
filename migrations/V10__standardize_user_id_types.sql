-- Standardize user_id column types across all tables to BIGINT
-- This ensures consistency and follows best practices for Telegram user IDs

-- Update transactions table
ALTER TABLE transactions 
ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;

-- Update categories table  
ALTER TABLE categories 
ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint;

-- Update users table (should already be BIGINT, but ensuring consistency)
-- Note: users table user_id is already BIGINT, so this is just for documentation

-- Add comments to document the standardization
COMMENT ON COLUMN transactions.user_id IS 'Telegram user ID (BIGINT) - consistent across all tables';
COMMENT ON COLUMN categories.user_id IS 'Telegram user ID (BIGINT) - consistent across all tables';
COMMENT ON COLUMN users.user_id IS 'Telegram user ID (BIGINT) - consistent across all tables'; 