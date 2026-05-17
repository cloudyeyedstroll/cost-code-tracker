import os
from database import get_cost_codes, supabase

def ensure_cost_code():
    df = get_cost_codes()
    if '99-000' in df['code_number'].values:
        print("Cost code 99-000 exists.")
    else:
        print("Cost code 99-000 missing. Inserting...")
        try:
            supabase.table('cost_codes').insert({
                "code_number": "99-000",
                "description": "Force Account / T&M"
            }).execute()
            print("Successfully inserted 99-000.")
        except Exception as e:
            print(f"Error inserting cost code: {e}")

if __name__ == "__main__":
    ensure_cost_code()
