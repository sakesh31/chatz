import os
from huggingface_hub import InferenceClient
from pymongo import MongoClient
import pyttsx3
import speech_recognition as sr
import sys
import platform
import threading
import datetime
import hashlib
import re

# Set Hugging Face API key
os.environ["HF_TOKEN"] = "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"

# MongoDB setup
mongo_client = MongoClient("mongodb+srv://abbulu:abbulu.31@chatz.jda0snt.mongodb.net/?retryWrites=true&w=majority&appName=chatz")
db = mongo_client["chatz"]
collection = db["conversations"]

# Hugging Face Inference Client setup
client = InferenceClient(
    provider="novita",
    api_key=os.environ["HF_TOKEN"],
)

MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

# Text-to-Speech engine
engine = pyttsx3.init()
speech_enabled = True

def speak(text):
    print("(Press Enter to stop speaking)")
    stop_flag = threading.Event()

    def wait_for_enter():
        if platform.system() == "Windows":
            import msvcrt
            while not stop_flag.is_set():
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b'\r':  # Enter key
                        engine.stop()
                        break
        else:
            import select
            while not stop_flag.is_set():
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    input()
                    engine.stop()
                    break

    listener = threading.Thread(target=wait_for_enter, daemon=True)
    listener.start()
    engine.say(text)
    engine.runAndWait()
    stop_flag.set()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... (speak now)")
        audio = r.listen(source, timeout=5, phrase_time_limit=15)
    try:
        text = r.recognize_google(audio)
        print(f"You (speech): {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand your speech.")
        return None
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return None

def ask_llama(messages):
    # messages: list of {role, content}
    completion = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages,
    )
    return completion.choices[0].message.content

def list_conversations():
    print("\n--- Conversation History ---")
    sessions = list(collection.find())
    if not sessions:
        print("No previous conversations found.")
        return []
    for idx, session in enumerate(sessions):
        start = session.get('start_time', 'unknown')
        name = session.get('name', 'Untitled')
        print(f"{idx+1}. [{name}] Started: {start} | {len(session['history'])} exchanges")
    print("---------------------------\n")
    return sessions

def show_conversation(session):
    name = session.get('name', 'Untitled')
    print(f"\n--- Conversation: {name} | Started at {session.get('start_time', 'unknown')} ---")
    for i, pair in enumerate(session['history']):
        print(f"{i+1}. You: {pair['question']}")
        print(f"   Assistant: {pair['answer']}\n")
    print("---------------------------------------------\n")

def set_password():
    while True:
        pw = input("Set a password for this conversation (min 4 chars, leave blank for none): ").strip()
        if not pw:
            return None
        if len(pw) < 4:
            print("Password must be at least 4 characters.")
            continue
        pw2 = input("Confirm password: ").strip()
        if pw != pw2:
            print("Passwords do not match.")
            continue
        return hashlib.sha256(pw.encode()).hexdigest()

def check_password(stored_hash):
    for _ in range(3):
        pw = input("Enter password for this conversation: ").strip()
        if hashlib.sha256(pw.encode()).hexdigest() == stored_hash:
            return True
        print("Incorrect password.")
    print("Too many failed attempts. Returning to main menu.")
    return False

def is_url(text):
    return bool(re.search(r'https?://\S+', text))

def extract_urls(text):
    return re.findall(r'(https?://\S+)', text)

def main():
    print("Welcome to chatz! Type 'exit' to quit.")
    print("You can decide for each answer if it should be spoken!")
    print("On startup, you can start a new conversation or continue a previous one.")
    print("Type 'delete' to delete a conversation, 'rename <number>' to rename a conversation.")
    print("Type 'history' to view all conversations.")
    print("Type 'file <path>' to share a file with chatz.")
    # Choose session
    while True:
        sessions = list_conversations()
        if sessions:
            choice = input("Start new conversation (n), continue previous (number), delete/rename (delete/rename <number>): ").strip().lower()
        else:
            choice = 'n'
        if choice == 'n':
            name = input("Enter a name for this conversation (or leave blank for 'Untitled'): ").strip()
            if not name:
                name = 'Untitled'
            session = {
                'start_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'name': name,
                'history': []
            }
            session_id = collection.insert_one(session).inserted_id
            session = collection.find_one({'_id': session_id})
            break
        elif choice == 'delete':
            sessions = list_conversations()
            if not sessions:
                continue
            num = input("Enter the number of the conversation to delete: ").strip()
            try:
                idx = int(num) - 1
                session_to_delete = sessions[idx]
                confirm = input(f"Delete conversation '{session_to_delete.get('name', 'Untitled')}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    collection.delete_one({'_id': session_to_delete['_id']})
                    print("Conversation deleted.\n")
                else:
                    print("Delete cancelled.\n")
            except:
                print("Invalid number.\n")
            continue
        elif choice.startswith('rename '):
            try:
                idx = int(choice.split()[1]) - 1
                session_to_rename = sessions[idx]
                new_name = input("Enter new name: ").strip()
                if new_name:
                    collection.update_one({'_id': session_to_rename['_id']}, {'$set': {'name': new_name}})
                    print("Conversation renamed.\n")
                else:
                    print("Rename cancelled.\n")
            except:
                print("Invalid number.\n")
            continue
        else:
            try:
                idx = int(choice) - 1
                session = sessions[idx]
                # Check for password
                if 'password' in session:
                    if not check_password(session['password']):
                        continue
                break
            except:
                print("Invalid choice.\n")
                continue
    # Show previous exchanges if continuing
    if session['history']:
        show_conversation(session)
    last_answer = None
    # Build messages for context
    messages = []
    # Add system prompt so assistant knows its name is chatz
    messages.append({'role': 'system', 'content': "You are an AI assistant named chatz. If the user addresses you as 'chatz', respond as if it's your name."})
    for pair in session['history']:
        messages.append({'role': 'user', 'content': pair['question']})
        messages.append({'role': 'assistant', 'content': pair['answer']})
    while True:
        mode = input("Speak or type your question? (s/t): ").strip().lower()
        if mode == 's':
            question = listen()
            if not question:
                print("Falling back to text input.")
                question = input("You: ")
        else:
            question = input("You: ")
        if question.lower() in ("exit", "quit"):
            # At end, ask if want to set password
            if 'password' not in session:
                pw_hash = set_password()
                if pw_hash:
                    collection.update_one({'_id': session['_id']}, {'$set': {'password': pw_hash}})
                    print("Password set for this conversation.\n")
            break
        if question.lower() == 'history':
            list_conversations()
            continue
        if question.lower() == 'delete':
            sessions = list_conversations()
            if not sessions:
                continue
            num = input("Enter the number of the conversation to delete: ").strip()
            try:
                idx = int(num) - 1
                session_to_delete = sessions[idx]
                confirm = input(f"Delete conversation '{session_to_delete.get('name', 'Untitled')}'? (y/n): ").strip().lower()
                if confirm == 'y':
                    collection.delete_one({'_id': session_to_delete['_id']})
                    print("Conversation deleted.\n")
                else:
                    print("Delete cancelled.\n")
            except:
                print("Invalid number.\n")
            continue
        if question.lower() == 'speak now':
            if last_answer:
                speak(last_answer)
            else:
                print("No previous answer to speak.\n")
            continue
        # File sharing
        if question.lower().startswith('file '):
            file_path = question[5:].strip('"')
            if os.path.isfile(file_path):
                file_info = {'file_name': os.path.basename(file_path), 'file_path': os.path.abspath(file_path)}
                print(f"File '{file_info['file_name']}' shared with chatz.")
                session['history'].append({'question': f"[File shared: {file_info['file_name']}]", 'answer': f"File received: {file_info['file_name']} at {file_info['file_path']}"})
                collection.update_one({'_id': session['_id']}, {'$set': {'history': session['history']}})
            else:
                print("File not found.")
            continue
        # Add user message to context
        messages.append({'role': 'user', 'content': question})
        answer = ask_llama(messages)
        # URL support: print URLs as clickable links
        def format_urls(text):
            urls = extract_urls(text)
            for url in urls:
                text = text.replace(url, f"<{url}>")
            return text
        print(f"chatz: {format_urls(answer)}\n")
        last_answer = answer
        speak_pref = input("Should I speak the answer? (y/n): ").strip().lower()
        if speak_pref == 'y':
            speak(answer)
        # Add to session history
        # If user message contains a URL, store as clickable
        user_q = question
        if is_url(question):
            urls = extract_urls(question)
            for url in urls:
                user_q = user_q.replace(url, f"<{url}>")
        session['history'].append({'question': user_q, 'answer': format_urls(answer)})
        # Add assistant message to context
        messages.append({'role': 'assistant', 'content': answer})
        # Update session in DB
        collection.update_one({'_id': session['_id']}, {'$set': {'history': session['history']}})

if __name__ == "__main__":
    main() 