-- 示例MySQL数据库建表语句
-- 运行此脚本创建示例表和数据

-- 创建数据库
CREATE DATABASE IF NOT EXISTS askdata DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE askdata;

-- 创建产品表
CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2),
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    product_id INT,
    quantity INT,
    total_amount DECIMAL(10, 2),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- 插入示例数据
INSERT INTO products (product_name, category, price, stock) VALUES
('iPhone 15', '电子产品', 6999.00, 100),
('MacBook Pro', '电子产品', 14999.00, 50),
('AirPods Pro', '配件', 1899.00, 200),
('iPad Air', '电子产品', 4799.00, 80),
('Apple Watch', '配件', 2999.00, 150);

INSERT INTO users (username, email) VALUES
('张三', 'zhangsan@example.com'),
('李四', 'lisi@example.com'),
('王五', 'wangwu@example.com');

INSERT INTO orders (user_id, product_id, quantity, total_amount) VALUES
(1, 1, 1, 6999.00),
(1, 3, 2, 3798.00),
(2, 2, 1, 14999.00),
(3, 4, 1, 4799.00),
(2, 5, 1, 2999.00);
