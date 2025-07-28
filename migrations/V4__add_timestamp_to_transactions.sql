ALTER TABLE transactions 
ADD COLUMN timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing records to have a timestamp (optional, but recommended)
UPDATE transactions 
SET timestamp = CURRENT_TIMESTAMP 
WHERE timestamp IS NULL; 