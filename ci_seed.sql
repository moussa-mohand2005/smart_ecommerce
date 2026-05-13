INSERT INTO shops (shop_id, shop_name, platform, shop_url, geography, traffic_estimate)
VALUES
    (1, 'Urban Threads', 'shopify', 'https://example.com/urban', 'USA', 25000),
    (2, 'Style Hub', 'woocommerce', 'https://example.com/stylehub', 'UK', 18000)
ON DUPLICATE KEY UPDATE shop_name=VALUES(shop_name);

INSERT INTO products (
    external_product_id, shop_id, product_url, category, subcategory, brand,
    product_name, description_raw, short_description, current_price, currency,
    rating_avg, reviews_count, stock_status, image_url_main, material,
    sole_type, closure, gender, season, style_type, is_enriched, scraped_at
)
VALUES
    ('ci-001', 1, 'https://example.com/p/1', 'Footwear', 'Sneakers', 'Urban Threads', 'Runner Air Mesh', 'Light mesh running sneaker', 'Light running sneaker', 69.90, 'USD', 4.8, 320, 'in_stock', NULL, 'Mesh', 'Rubber', 'Laces', 'unisex', 'All-Season', 'Athletic', TRUE, NOW()),
    ('ci-002', 1, 'https://example.com/p/2', 'Footwear', 'Boots', 'Urban Threads', 'Urban Leather Boot', 'Leather ankle boot', 'Leather city boot', 129.00, 'USD', 4.6, 185, 'in_stock', NULL, 'Leather', 'Rubber', 'Laces', 'men', 'Fall', 'Casual', TRUE, NOW()),
    ('ci-003', 1, 'https://example.com/p/3', 'Clothing', 'T-Shirts', 'Urban Threads', 'Classic Cotton Tee', 'Soft cotton crew neck tee', 'Classic cotton tee', 24.50, 'USD', 4.3, 210, 'in_stock', NULL, 'Cotton', 'Regular', 'Pull-on', 'unisex', 'All-Season', 'Casual', TRUE, NOW()),
    ('ci-004', 1, 'https://example.com/p/4', 'Clothing', 'Hoodies', 'Urban Threads', 'Fleece Pullover Hoodie', 'Warm fleece hoodie with kangaroo pocket', 'Fleece pullover hoodie', 59.00, 'USD', 4.5, 175, 'in_stock', NULL, 'Cotton-Polyester', 'Relaxed', 'Pull-on', 'unisex', 'Winter', 'Streetwear', TRUE, NOW()),
    ('ci-005', 2, 'https://example.com/p/5', 'Clothing', 'Jackets', 'Style Hub', 'Denim Trucker Jacket', 'Classic denim trucker jacket', 'Denim trucker jacket', 88.00, 'USD', 4.7, 310, 'in_stock', NULL, 'Denim', 'Regular', 'Button', 'men', 'Spring', 'Casual', TRUE, NOW()),
    ('ci-006', 2, 'https://example.com/p/6', 'Clothing', 'Dresses', 'Style Hub', 'Floral Midi Dress', 'Floral print midi wrap dress', 'Floral midi dress', 65.00, 'USD', 4.4, 140, 'in_stock', NULL, 'Rayon', 'Regular', 'Wrap', 'women', 'Summer', 'Bohemian', TRUE, NOW()),
    ('ci-007', 2, 'https://example.com/p/7', 'Footwear', 'Heels', 'Style Hub', 'Evening Block Heel', 'Comfort block heel for events', 'Block heel', 99.00, 'USD', 4.2, 75, 'in_stock', NULL, 'Synthetic', 'Rubber', 'Buckle', 'women', 'All-Season', 'Formal', TRUE, NOW()),
    ('ci-008', 2, 'https://example.com/p/8', 'Clothing', 'Pants', 'Style Hub', 'Slim Fit Chinos', 'Stretch slim fit chinos', 'Slim chinos', 49.00, 'USD', 4.1, 130, 'in_stock', NULL, 'Cotton-Stretch', 'Slim', 'Zip', 'men', 'All-Season', 'Casual', TRUE, NOW())
ON DUPLICATE KEY UPDATE product_name=VALUES(product_name);
