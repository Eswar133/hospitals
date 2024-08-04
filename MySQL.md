# MySQL Installation and Setup on Ubuntu 20.04

## Step 1 — Installing MySQL

1. **Update the package index:**
   ```bash
   sudo apt update
   
2. **Install MYSQL server:**
   ```bash
   sudo apt install mysql-server
   
3. **sudo systemctl start mysql.service**
   ```bash
   sudo systemctl start mysql.service
   
## Step 2 — Configuring MySQL

1. **Opent the MySQL prompt:**
   ```bash
   sudo mysql
   
2. **Change root user authentication to use a password:**
   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
   
3. **Exit MySQL:**
   ```sql
   exit
   
4. **Run the MySQL secure installation script:**
   ```bash
   sudo mysql_secure_installation
   ```
    **Follow the prompts to set up the Validate Password Plugin (optional), set a root     
    password, and secure your MySQL installation.**

5. **Change root user authentication back to auth_socket:**
   ```bash
   mysql -u root -p
   ALTER USER 'root'@'localhost' IDENTIFIED WITH auth_socket;
   
## step 3  — Creating a Dedicated MySQL User and Granting Privileges

1. **Access the MySQL prompt:**
   ```bash
   sudo mysql
   
2. **Create a new MySQL user:**
   ```sql
   CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';
   ```
   **For compatibility with PHP applications, use:**
   ```sql
   CREATE USER 'username'@'localhost' IDENTIFIED WITH mysql_native_password BY   
   'password';
   
3. **Grant privileges to the new user:**
   ```sql
   GRANT CREATE, ALTER, DROP, INSERT, UPDATE, INDEX, DELETE, SELECT, REFERENCES, RELOAD 
   ON *.* TO 'username'@'localhost' WITH GRANT OPTION;
   ```
   **Or grant all privileges:**
   ```sql
   GRANT ALL PRIVILEGES ON *.* TO 'username'@'localhost' WITH GRANT OPTION;
   
4. **Flush privileges to apply changes:**
   ```sql
   FLUSH PRIVILEGES;
   ```
   **FLUSH PRIVILEGES**
   
6. **Exit the MySQL client**
   ```sql
   exit
   
7. **Log in with the new user:**
   ```bash
   mysql -u username -p
   
## Step 4 — Testing MySQL

1 **Check MySQL status:**
   ```bash
     systemct1 status mysql.service
   ```
   **You should see the status as active (running)**
   ```css
   
This markdown should be ready to use in a GitHub repository for clear, formatted instructions. Adjust `username` and `password` as needed.

   
   

   
   
   
   
   
