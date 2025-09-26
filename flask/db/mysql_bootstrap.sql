-- Adjust names/passwords as needed BEFORE running this.
-- Example DB name: qr_ordering
-- Example user:    qr_user
-- Example pass:    replace-with-a-strong-password

CREATE DATABASE IF NOT EXISTS `qr_ordering`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create the user for common hosts you might use (localhost, 127.0.0.1, and any host)
CREATE USER IF NOT EXISTS 'qr_user'@'localhost' IDENTIFIED BY 'replace-with-a-strong-password';
CREATE USER IF NOT EXISTS 'qr_user'@'127.0.0.1' IDENTIFIED BY 'replace-with-a-strong-password';
CREATE USER IF NOT EXISTS 'qr_user'@'%' IDENTIFIED BY 'replace-with-a-strong-password';

GRANT ALL PRIVILEGES ON `qr_ordering`.* TO 'qr_user'@'localhost';
GRANT ALL PRIVILEGES ON `qr_ordering`.* TO 'qr_user'@'127.0.0.1';
GRANT ALL PRIVILEGES ON `qr_ordering`.* TO 'qr_user'@'%';

FLUSH PRIVILEGES;

-- If you run into auth plugin issues with older drivers, you can switch the plugin:
-- ALTER USER 'qr_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'replace-with-a-strong-password';
-- ALTER USER 'qr_user'@'127.0.0.1' IDENTIFIED WITH mysql_native_password BY 'replace-with-a-strong-password';
-- ALTER USER 'qr_user'@'%' IDENTIFIED WITH mysql_native_password BY 'replace-with-a-strong-password';
