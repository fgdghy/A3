export DB_HOST="bookstore-db-dev-instance1.c2qxlb8d3arf.us-east-1.rds.amazonaws.com"

mysql -h $DB_HOST -u admin -p'12345678' -e "
    USE customers_db; 
    SET FOREIGN_KEY_CHECKS = 0; 
    TRUNCATE TABLE customers; 
    SET FOREIGN_KEY_CHECKS = 1;

    USE book_db; 
    SET FOREIGN_KEY_CHECKS = 0; 
    TRUNCATE TABLE related_books; 
    TRUNCATE TABLE books; 
    SET FOREIGN_KEY_CHECKS = 1;
"