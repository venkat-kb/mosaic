import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
import pywhatkit
import time

# This allows the script to find your other modules like 'db'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase import create_supabase_client

# --- INITIALIZATION ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_supabase_client()
model = genai.GenerativeModel("gemini-pro")


def send_message(phone_number: str, message: str):
    """
    Safely sends a WhatsApp message using pywhatkit.
    """
    try:
        print(f"\n[WhatsApp] Preparing to send message to {phone_number}...")
        pywhatkit.sendwhatmsg_instantly(
            phone_no=phone_number,
            message=message,
            wait_time=20,  # Increased wait time for reliability
            tab_close=True
        )
        print("[WhatsApp] Message sent successfully via WhatsApp Web.")
        time.sleep(5) # Give the browser a moment to close
    except Exception as e:
        print(f"[WhatsApp] FAILED TO SEND MESSAGE: {e}")
        print("[WhatsApp] Please ensure you are logged into WhatsApp Web in your default browser.")


def generate_contextual_reply(user_message: str, case_history: list) -> str:
    """Uses Gemini to generate a reply based on the user's message and their case history."""
    
    history_str = "\n".join([
        f"- Case ID: {case.get('case_no')}, Status: {case.get('status')}, Details: '{case.get('detail')}'"
        for case in case_history
    ]) if case_history else "No open cases found for this user."

    prompt = f"""
    You are a helpful and concise assistant for a citizen grievance redressal system.
    A user has sent a message regarding their complaint. Your task is to provide a helpful response
    based on their message and their case history from the database.

    USER'S MESSAGE: "{user_message}"

    USER'S CASE HISTORY FROM DATABASE:
    {history_str}

    Based on the context, provide a clear, brief, and friendly reply.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[AI Error] Could not generate reply: {e}")
        return "I'm sorry, I'm having trouble connecting to my system right now. Please try again later."


def main():
    """Main function to run the interactive conversation manager."""
    print("--- Mosaic: Interactive WhatsApp Conversation Manager ---")
    print("\nWARNING: This tool automates WhatsApp Web and carries a risk of your number being banned.")
    print("Ensure you are logged into WhatsApp Web in your browser before starting.")
    print("-" * 55)

    # --- Step 1: Get Initial Details ---
    phone_number = input("Enter the user's full phone number (e.g., +919876543210): ")
    name = input(f"Enter the user's name: ")

    # --- Step 2: Send the Initial Registration Message ---
    initial_message = f"Hello {name}, thanks for registering your complaint with Mosaic!"
    send_message(phone_number, initial_message)

    print("\n--- Conversation Started. Waiting for user replies... ---")

    # --- Step 3: Enter the Conversational Loop ---
    while True:
        print("\n" + "="*55)
        user_reply = input("Enter the user's latest reply (or press Enter to exit): ")
        
        if not user_reply:
            print("Exiting conversation manager. Goodbye!")
            break

        # Fetch context from Supabase
        print(f"\nFetching case history for {phone_number}...")
        # Clean the phone number for database lookup
        db_phone_number = phone_number.replace("+91", "").strip()
        response = supabase.table("Complaint").select("*").eq("phone_no", db_phone_number).execute()
        case_history = response.data if response.data else []

        if not case_history:
            print("No history found for this number in the database.")

        # Generate the AI-powered reply
        print("Generating AI-powered reply...")
        ai_reply = generate_contextual_reply(user_reply, case_history)
        print(f"\nSUGGESTED REPLY: \n---\n{ai_reply}\n---")

        # Confirm before sending
        confirm = input("Do you want to send this reply? (y/n): ").lower()
        if confirm == 'y':
            send_message(phone_number, ai_reply)
        else:
            print("Reply cancelled.")

if __name__ == "__main__":
    main()