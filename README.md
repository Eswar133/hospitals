# hospitals
This project is an implementation of REST API endpoints to handle user management operations including signup, login, dashboard access, and logout.

# API ENDPOINTS
## Signup
- Request Method: POST
- Sample Endpoint: http://localhost:8000/signup/
- Sample Input: ``` {
  "first_name": "John",
  "last_name": "Doe",
  "profile_picture": "eswar.png",
  "username": "johndoe",
  "email": "johndoe@example.com",
  "password": "password123",
  "confirm_password": "password123",
  "address_line1": "123 Main St",
  "city": "Springfield",
  "state": "IL",
  "pincode": "62701",
  "user_type": "patient"
} ```
- Sample Output : ``` { "redirect":/login/} ```
- Response Code : 200

## Login
- Request Method: POST
- Sample Endpoint: http://localhost:8000/login/
- Sample Input: ```{
  "username": "johndoe",
  "password": "password123",
  "user_type": "patient"
} ```
- Sample Output: ```{
  "redirect": "/patient_dashboard/"
}```
- Response Code: 200

## Patient Dashboard
- Request Method: GET
- Sample Endpoint: http://localhost:8000/patient_dashboard/
- Sample Output: (Rendered HTML with user's profile information)
- Response Code: 200

## Doctor Dashboard
- Request Method: GET
- Sample Endpoint: http://localhost:8000/doctor_dashboard/
- Sample Output: (Rendered HTML with user's profile information)
- Response Code: 200

## Logout
- Request Method: GET
- Sample Endpoint: http://localhost:8000/logout/
- Sample Output: ``` {
  "redirect": "/login/"
}  ```
- Response Code: 302 (Redirect)

# TECH STACK
## Languages and Frameworks
- Python
- Django (v4)

## Libraries and Tools
- Django's built-in authentication system
-  SQLite (default database)
  
# Installation
- Link : https://github.com/Eswar133/hospitals/blame/main/Installation.md
