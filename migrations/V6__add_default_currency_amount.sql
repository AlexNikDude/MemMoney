ALTER TABLE transactions 
ADD COLUMN default_currency_amount DECIMAL(10,2);

-- Add a comment to explain the column purpose
COMMENT ON COLUMN transactions.default_currency_amount IS 'Amount converted to user''s default currency for consistent reporting'; 