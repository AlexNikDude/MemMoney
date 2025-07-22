CREATE TABLE IF NOT EXISTS categories (
    id BIGSERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

ALTER TABLE transactions
ADD COLUMN category_id BIGINT REFERENCES categories(id); 