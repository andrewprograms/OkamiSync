DDL = [
    """
    CREATE TABLE IF NOT EXISTS carts (
      id CHAR(36) PRIMARY KEY,
      table_id INT NOT NULL,
      created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
      KEY idx_carts_table (table_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS cart_items (
      id CHAR(36) PRIMARY KEY,
      cart_id CHAR(36) NOT NULL,
      item_id CHAR(36) NOT NULL,
      quantity INT NOT NULL DEFAULT 1,
      options JSON NULL,
      notes VARCHAR(280) NULL,
      added_by VARCHAR(64) NOT NULL,
      state VARCHAR(16) NOT NULL DEFAULT 'in_cart',
      created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY idx_ci_cart (cart_id),
      KEY idx_ci_item (item_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS orders (
      id CHAR(36) PRIMARY KEY,
      table_id INT NOT NULL,
      state VARCHAR(16) NOT NULL DEFAULT 'submitted',
      subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
      tax DECIMAL(10,2) NOT NULL DEFAULT 0,
      service_charge DECIMAL(10,2) NOT NULL DEFAULT 0,
      discount_total DECIMAL(10,2) NOT NULL DEFAULT 0,
      total DECIMAL(10,2) NOT NULL DEFAULT 0,
      created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      menu_version VARCHAR(64) NULL,
      ticket_seconds INT NULL,
      KEY idx_orders_table (table_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS order_items (
      id CHAR(36) PRIMARY KEY,
      order_id CHAR(36) NOT NULL,
      item_id CHAR(36) NOT NULL,
      title_snapshot VARCHAR(255) NOT NULL,
      quantity INT NOT NULL DEFAULT 1,
      price_each DECIMAL(10,2) NOT NULL DEFAULT 0,
      options JSON NULL,
      notes VARCHAR(280) NULL,
      state VARCHAR(16) NOT NULL DEFAULT 'submitted',
      created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
      KEY idx_oi_order (order_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS order_events (
      id INT AUTO_INCREMENT PRIMARY KEY,
      order_id CHAR(36) NOT NULL,
      order_item_id CHAR(36) NULL,
      actor_user_id CHAR(36) NULL,
      actor_table_user VARCHAR(64) NULL,
      action VARCHAR(32) NOT NULL,
      reason VARCHAR(255) NULL,
      created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
      KEY idx_oe_order (order_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
]
