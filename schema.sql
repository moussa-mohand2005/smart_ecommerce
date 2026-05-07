CREATE TABLE IF NOT EXISTS shops (
    shop_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_name VARCHAR(255) NOT NULL UNIQUE,
    platform VARCHAR(50),
    shop_url TEXT,
    geography VARCHAR(100),
    traffic_estimate INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    external_product_id VARCHAR(255),
    shop_id INT NOT NULL,
    product_url TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(255),
    product_name VARCHAR(500),
    description_raw TEXT,
    short_description VARCHAR(500),
    current_price DECIMAL(12, 2),
    currency VARCHAR(10),
    rating_avg DECIMAL(4, 2),
    reviews_count INT DEFAULT 0,
    stock_status VARCHAR(50),
    image_url_main TEXT,
    material VARCHAR(255),
    sole_type VARCHAR(255),
    closure VARCHAR(255),
    gender VARCHAR(50),
    persona_json JSON,
    is_enriched BOOLEAN DEFAULT FALSE,
    ml_score DECIMAL(8, 4),
    predicted_success DECIMAL(8, 4),
    cluster_id INT DEFAULT 0,
    pca_x DOUBLE DEFAULT 0,
    pca_y DOUBLE DEFAULT 0,
    scraped_at DATETIME,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_shop_external_product (shop_id, external_product_id),
    INDEX idx_products_enriched_score (is_enriched, ml_score),
    INDEX idx_products_cluster (cluster_id),
    CONSTRAINT fk_products_shop
        FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
        ON DELETE CASCADE
);
