INSERT INTO shops (shop_id, shop_name, platform, shop_url, geography, traffic_estimate)
VALUES
    (1, 'Atlas Shoes', 'shopify', 'https://example.com/atlas', 'Morocco', 12000),
    (2, 'Gulf Sneakers', 'woocommerce', 'https://example.com/gulf', 'UAE', 18000)
ON DUPLICATE KEY UPDATE shop_name=VALUES(shop_name);

INSERT INTO products (
    external_product_id, shop_id, product_url, category, subcategory, brand,
    product_name, description_raw, short_description, current_price, currency,
    rating_avg, reviews_count, stock_status, image_url_main, material,
    sole_type, closure, gender, is_enriched, scraped_at
)
VALUES
    ('ci-001', 1, 'https://example.com/p/1', 'Shoes', 'Sneakers', 'Atlas', 'Runner Air Mesh', 'Light mesh running sneaker', 'Light running sneaker', 69.90, 'USD', 4.8, 320, 'in_stock', NULL, 'Mesh', 'Rubber', 'Laces', 'unisexe', TRUE, NOW()),
    ('ci-002', 1, 'https://example.com/p/2', 'Shoes', 'Boots', 'Atlas', 'Urban Leather Boot', 'Leather ankle boot', 'Leather city boot', 129.00, 'USD', 4.6, 185, 'in_stock', NULL, 'Leather', 'Rubber', 'Laces', 'homme', TRUE, NOW()),
    ('ci-003', 1, 'https://example.com/p/3', 'Shoes', 'Sandals', 'Atlas', 'Summer Slide', 'Casual slide sandal', 'Casual slide', 34.50, 'USD', 4.1, 96, 'in_stock', NULL, 'Synthetic', 'Foam', 'Slip-on', 'femme', TRUE, NOW()),
    ('ci-004', 1, 'https://example.com/p/4', 'Shoes', 'Sneakers', 'Atlas', 'Court Classic', 'Classic court sneaker', 'Court sneaker', 79.00, 'USD', 4.4, 210, 'out_of_stock', NULL, 'Leather', 'Rubber', 'Laces', 'unisexe', TRUE, NOW()),
    ('ci-005', 2, 'https://example.com/p/5', 'Shoes', 'Sneakers', 'Gulf', 'Desert Knit Runner', 'Breathable knit runner', 'Knit runner', 88.00, 'USD', 4.9, 510, 'in_stock', NULL, 'Knit', 'Rubber', 'Laces', 'unisexe', TRUE, NOW()),
    ('ci-006', 2, 'https://example.com/p/6', 'Shoes', 'Loafers', 'Gulf', 'Premium Suede Loafer', 'Soft suede loafer', 'Suede loafer', 115.00, 'USD', 4.5, 140, 'in_stock', NULL, 'Suede', 'Leather', 'Slip-on', 'homme', TRUE, NOW()),
    ('ci-007', 2, 'https://example.com/p/7', 'Shoes', 'Heels', 'Gulf', 'Evening Block Heel', 'Comfort block heel', 'Block heel', 99.00, 'USD', 4.2, 75, 'in_stock', NULL, 'Synthetic', 'Rubber', 'Buckle', 'femme', TRUE, NOW()),
    ('ci-008', 2, 'https://example.com/p/8', 'Shoes', 'Sneakers', 'Gulf', 'Everyday Canvas Low', 'Canvas low sneaker', 'Canvas sneaker', 49.00, 'USD', 4.0, 130, 'in_stock', NULL, 'Canvas', 'Rubber', 'Laces', 'unisexe', TRUE, NOW())
ON DUPLICATE KEY UPDATE product_name=VALUES(product_name);
