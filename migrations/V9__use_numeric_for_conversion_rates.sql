-- Drop the existing table and recreate with NUMERIC type for unlimited precision
DROP TABLE IF EXISTS conversion_rates;

CREATE TABLE conversion_rates (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    from_currency VARCHAR(3) NOT NULL,
    to_currency VARCHAR(3) NOT NULL,
    rate NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for better query performance
CREATE INDEX idx_conversion_rates_date ON conversion_rates(date);
CREATE INDEX idx_conversion_rates_currencies ON conversion_rates(from_currency, to_currency);
CREATE INDEX idx_conversion_rates_lookup ON conversion_rates(date, from_currency, to_currency);

-- Add unique constraint to prevent duplicate rates for the same date and currency pair
ALTER TABLE conversion_rates 
ADD CONSTRAINT unique_conversion_rate UNIQUE (date, from_currency, to_currency);

-- Add comments to explain the table and columns
COMMENT ON TABLE conversion_rates IS 'Stores daily currency conversion rates for transaction amount conversion';
COMMENT ON COLUMN conversion_rates.date IS 'Date for which the conversion rate is valid';
COMMENT ON COLUMN conversion_rates.from_currency IS 'Source currency code (3 letters)';
COMMENT ON COLUMN conversion_rates.to_currency IS 'Target currency code (3 letters)';
COMMENT ON COLUMN conversion_rates.rate IS 'Conversion rate from from_currency to to_currency (unlimited precision)';
COMMENT ON COLUMN conversion_rates.created_at IS 'Timestamp when this rate was added to the database'; 