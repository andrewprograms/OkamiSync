DDL = [
    """
    CREATE TABLE IF NOT EXISTS categories (
      id CHAR(36) PRIMARY KEY,
      parent_id CHAR(36) NULL,
      title_i18n JSON NULL,
      description_i18n JSON NULL,
      sort_order INT NOT NULL DEFAULT 0,
      active TINYINT(1) NOT NULL DEFAULT 1
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS items (
      id CHAR(36) PRIMARY KEY,
      category_id CHAR(36) NULL,
      title_i18n JSON NULL,
      description_i18n JSON NULL,
      price DECIMAL(10,2) NOT NULL,
      tax_class VARCHAR(32) NOT NULL DEFAULT 'standard',
      dietary_tags JSON NULL,
      availability JSON NULL,
      sort_order INT NOT NULL DEFAULT 0,
      image_path VARCHAR(255) NULL,
      is_86 TINYINT(1) NOT NULL DEFAULT 0,
      active TINYINT(1) NOT NULL DEFAULT 1,
      KEY idx_items_category (category_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS option_groups (
      id CHAR(36) PRIMARY KEY,
      item_id CHAR(36) NOT NULL,
      name_i18n JSON NULL,
      required TINYINT(1) NOT NULL DEFAULT 0,
      min_qty INT NOT NULL DEFAULT 0,
      max_qty INT NOT NULL DEFAULT 3,
      KEY idx_optgrp_item (item_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS options (
      id CHAR(36) PRIMARY KEY,
      group_id CHAR(36) NOT NULL,
      name_i18n JSON NULL,
      price_delta DECIMAL(10,2) NOT NULL DEFAULT 0,
      max_per_item INT NOT NULL DEFAULT 3,
      is_exclusion TINYINT(1) NOT NULL DEFAULT 0,
      KEY idx_opt_group (group_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    ,
    """
    CREATE TABLE IF NOT EXISTS menu_versions (
      id INT AUTO_INCREMENT PRIMARY KEY,
      created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
      version_token VARCHAR(64) NOT NULL,
      KEY idx_mv_token (version_token)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
]
