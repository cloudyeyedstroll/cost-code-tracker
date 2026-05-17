from database import supabase
import pandas as pd

def list_users():
    res = supabase.table('employees').select('email, first_name, last_name, role, account_status').execute()
    for row in res.data:
        print(f"Email: {row['email']}, Name: {row['first_name']} {row['last_name']}, Role: {row['role']}, Status: {row['account_status']}")

if __name__ == "__main__":
    list_users()
