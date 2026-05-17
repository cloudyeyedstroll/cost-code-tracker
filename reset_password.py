import os
from database import supabase

def reset_admin_password():
    email = "admin2@example.com"
    new_password = "Password123!"
    
    # Get user auth_id from employees table
    res = supabase.table('employees').select('auth_id').eq('email', email).execute()
    if res.data and len(res.data) > 0:
        auth_id = res.data[0].get('auth_id')
        if auth_id:
            try:
                supabase.auth.admin.update_user_by_id(auth_id, {"password": new_password})
                print(f"Successfully reset password for {email} to: {new_password}")
            except Exception as e:
                print(f"Error resetting password: {e}")
        else:
            print("No auth_id found for this user. Maybe they weren't fully created in Auth?")
    else:
        print("User not found.")

if __name__ == "__main__":
    reset_admin_password()
