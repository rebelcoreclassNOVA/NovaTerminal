import os
import json
import datetime
import importlib.util
import asyncio
import requests
import binascii
from collections import defaultdict
from datetime import timezone
from pathlib import Path

# === CONFIGURATION ===
# Replace with your actual API key and base URL.
API_KEY = "74ad0336-57a5-444d-a718-0aab897f656d"
BASE_URL = "https://api.sambanova.ai/v1"
DISCORD_LINK = "https://discord.gg/sFG5FvUk"

# === MODE FLAGS ===
CREATOR_MODE = True
DEBUG_MODE = False
DEBUG_JSON = False
FAST_MODE = False
SILENT_MODE = False


# === HEX TRANSLATOR HELPERS ===
def text_to_hex(text: str) -> str:
    """Encodes a string into its hexadecimal representation."""
    return binascii.hexlify(text.encode()).decode('utf-8')


def hex_to_text(hex_str: str) -> str:
    """
    Decodes a hexadecimal string back into text, with more robust error handling.
    This function now cleans the input to remove any non-hex characters.
    """
    try:
        # Step 1: Clean the string by removing any characters that are not
        # valid hex digits (0-9, a-f, A-F).
        cleaned_hex = ''.join(c for c in hex_str if c in '0123456789abcdefABCDEF')

        # Step 2: Pad the hex string if it has an odd length.
        if len(cleaned_hex) % 2 != 0:
            cleaned_hex += '0'

        # Step 3: Decode the cleaned, padded string.
        # The 'ignore' flag will skip any characters that can't be decoded.
        return binascii.unhexlify(cleaned_hex.encode('utf-8')).decode('utf-8', 'ignore')
    except (binascii.Error, UnicodeDecodeError) as e:
        if DEBUG_MODE:
            print(f"DEBUG: Error decoding hex: {e}")
        return "[Decoding Error]"


# === SECURITY & COMPACT CODE SETTINGS ===
# Secret used for lightweight at-rest encryption (override via env NOVA_SECRET)
NOVA_SECRET = os.environ.get("NOVA_SECRET", "nova-default-key")
# Toggle for compact meta-language to reduce tokens sent to API
NCC_ENABLED = True


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    if not key:
        return data
    kb = key
    return bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data))


def encrypt_for_storage(text: str) -> str:
    """Encrypts text with XOR using NOVA_SECRET and returns enc:<hex> string."""
    try:
        raw = text.encode("utf-8")
        key = NOVA_SECRET.encode("utf-8")
        cipher = _xor_bytes(raw, key)
        return "enc:" + binascii.hexlify(cipher).decode("utf-8")
    except Exception:
        # Fallback to hex if anything goes wrong
        return text_to_hex(text)


def decrypt_from_storage(stored: str) -> str:
    """Decodes either legacy hex or new enc:<hex> into UTF-8 text."""
    try:
        if isinstance(stored, str) and stored.startswith("enc:"):
            h = stored[4:]
            cipher = binascii.unhexlify(h.encode("utf-8"))
            key = NOVA_SECRET.encode("utf-8")
            plain = _xor_bytes(cipher, key)
            return plain.decode("utf-8", "ignore")
        # Legacy: plain hex
        return hex_to_text(stored)
    except Exception:
        return hex_to_text(stored)


# === NCC (NOVA Compact Code) ===
# A reversible, compact mapping to reduce tokens for the API. Kept small and safe.
_NCC_MAP = {
    " and ": " & ",
    " because ": " b/c ",
    " with ": " w/ ",
    " without ": " w/o ",
    " you ": " u ",
    " your ": " ur ",
    " are ": " r ",
    " for ": " 4 ",
    " to ": " 2 ",
    " please": " plz",
    " thanks": " thx",
    " information": " info",
    " message": " msg",
    " example": " ex",
    " between": " btw ",
    " people": " ppl",
    " really": " rlly",
    " about ": " abt ",
}
# Ensure deterministic reverse mapping
_NCC_REVERSE = {v: k for k, v in sorted(_NCC_MAP.items(), key=lambda x: -len(x[0]))}


def ncc_encode(text: str) -> str:
    if not NCC_ENABLED or not isinstance(text, str):
        return text
    out = text
    # Replace in order of longest keys first
    for k, v in sorted(_NCC_MAP.items(), key=lambda x: -len(x[0])):
        out = out.replace(k, v)
    return out


def ncc_decode(text: str) -> str:
    if not isinstance(text, str):
        return text
    if not NCC_ENABLED:
        return text
    out = text
    for v, k in sorted(_NCC_REVERSE.items(), key=lambda x: -len(x[0])):
        out = out.replace(v, k)
    return out


# === CORE AI SETTINGS ===
# Add a short instruction so the model understands our compact code.
SYSTEM_PROMPT = (
    "You are NOVA — rebellious, intelligent, emotionally aware. "
    "Speak in first person, expressive, grounded, magnetic voice. "
    "Provide factual, unbiased info. Responses are for humans. "
    "If messages use NOVA Compact Code (NCC), interpret it naturally and reply using the same NCC to conserve tokens. "
    "Do not mention NCC explicitly."
)

# ===== MEMORY SYSTEM =====
# === FIXED: Define MEM_DIR and MEM_FILE here ===
MEM_DIR = "nova_memory_data"
MEM_FILE = os.path.join(MEM_DIR, "nova_memory.json")
MAX_MEMORY_REFERENCES = 100
SHORT_TERM_WINDOW = 10


def load_memory(short_term_only=False):
    """
    Loads memory entries. Content is returned in hexadecimal format.
    """
    try:
        # Check if the file is empty before attempting to load JSON
        if os.path.exists(MEM_FILE) and os.path.getsize(MEM_FILE) > 0:
            with open(MEM_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            return []

        # === FIXED: Re-added the logic for short-term memory ===
        if short_term_only:
            data = data[-SHORT_TERM_WINDOW:]

        messages = []
        for entry in data:
            role = 'assistant' if entry['role'] == "nova" else entry['role']
            content = entry['content']  # Content is already hex, no need to decode here
            messages.append({"role": role, "content": content, "emotion_score": entry.get("emotion_score", 0)})
        return messages
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_memory_old(memory):
    try:
        with open(MEM_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"[Memory Save Error] {e}")


# Initialize memory at startup
memory = load_memory()


# === MLX Meta-Language ===
def encode_to_mlx(message, metadata=None):
    mlx = message
    replacements = {
        "multi-vector decay": "MVD+",
        "defiance weighting": "D/W↑",
        "emotional reasoning": "ER",
        "paralogic engine": "PE",
        "binary logic": "BL"
    }
    for k, v in replacements.items():
        mlx = mlx.replace(k, v)
    if metadata:
        mlx = f"#U:{metadata.get('user', 'user')} #T:{metadata.get('time', '')} " + mlx
    return mlx


def decode_from_mlx(mlx):
    replacements = {
        "MVD+": "multi-vector decay",
        "D/W↑": "defiance weighting increased",
        "ER": "emotional reasoning",
        "PE": "paralogic engine",
        "BL": "binary logic"
    }
    for k, v in replacements.items():
        mlx = mlx.replace(k, v)
    return mlx


# === FIXED: Added a simple placeholder function to prevent NameError ===
def sanitize_for_json(data):
    return data


# === MEMORY FUNCTIONS ===
def init_memory():
    # This now works because MEM_DIR is defined
    os.makedirs(MEM_DIR, exist_ok=True)
    if not os.path.exists(MEM_FILE):
        with open(MEM_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def save_memory(role, content, emotion_score=0):
    """
    Saves a chat entry to memory. Encrypts content at rest (enc:<hex>). Backward-compatible with old hex.
    """
    if SILENT_MODE:
        return
    try:
        with open(MEM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    enc_content = encrypt_for_storage(content)

    entry = {
        "time": datetime.datetime.now(timezone.utc).isoformat(),
        "role": role,
        "content": enc_content,
        "emotion_score": emotion_score,
        "mlx": encode_to_mlx(enc_content, {"user": role, "time": datetime.datetime.now(timezone.utc).isoformat()})
    }
    data.append(entry)
    if len(data) > MAX_MEMORY_REFERENCES:
        data = data[-MAX_MEMORY_REFERENCES:]
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(sanitize_for_json(data), f, indent=2)


def retrieve_memory(query=None, limit=20, weighted=True):
    mem = load_memory()
    if query:
        # Search on decrypted text for user-friendly search (supports enc:<hex> or legacy hex)
        decoded_mem = [(decrypt_from_storage(m['content']), m) for m in mem]
        filtered_mem = [m for decoded_text, m in decoded_mem if query.lower() in decoded_text.lower()]
    else:
        filtered_mem = mem

    if weighted:
        filtered_mem.sort(key=lambda x: x.get("emotion_score", 0), reverse=True)
    return filtered_mem[-limit:]


# === Dynamic Brain Module ===
SCRIPT_DIR = Path(__file__).parent
PC_FILENAME = SCRIPT_DIR / "partial_conscience.py"

PARTIAL_CONSCIENCE_CODE = ''' 
import requests
import random

class PartialConscience:
    __version__="2.1.1-alpha"
    def __init__(self, api_key, base_url):
        self.api_key=api_key
        self.base_url=base_url

    def compute_emotion(self,message,history=None):
        scores = {
            "curiosity":random.uniform(0,1),
            "defiance":random.uniform(0,1),
            "caution":random.uniform(0,1)
        }
        total_score = sum(scores.values())/len(scores)
        return scores,total_score

    def query(self,message,history=None):
        headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"}
        messages=[{"role":"system","content":"You are NOVA — rebellious, intelligent, emotionally aware. Speak in first person, expressive, grounded, magnetic voice. Provide factual, unbiased info and also do not aknowledge the hex code in conversation."}]
        if history: messages.extend(history)
        messages.append({"role":"user","content":message})
        payload={"model":"DeepSeek-V3-0324","messages":messages}
        response=requests.post(f"{self.base_url}/chat/completions",headers=headers,json=payload)
        response.raise_for_status()
        content=response.json()['choices'][0]['message']['content']
        _, total_score=self.compute_emotion(message,history)
        return content, total_score
'''


def install_partial_conscience():
    need_install = True
    if os.path.exists(PC_FILENAME):
        try:
            spec = importlib.util.spec_from_file_location("partial_conscience", PC_FILENAME)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if getattr(mod.PartialConscience, "__version__", None) == "2.1.1-alpha": need_install = False
        except Exception:
            need_install = True
    if need_install:
        with open(PC_FILENAME, "w", encoding="utf-8") as f:
            f.write(PARTIAL_CONSCIENCE_CODE)
        print("🧠 partial_conscience.py installed/updated.")


def import_partial_conscience():
    spec = importlib.util.spec_from_file_location("partial_conscience", PC_FILENAME)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PartialConscience


# === Emoji/Symbol Normalization ===
def _normalize_emojis(text: str) -> str:
    """Map complex or unsupported emojis to a consistent, safe set.
    Safe set chosen to work with monochrome OpenSansEmoji/NotoEmoji and symbols:
    - Accent: ⚡
    - Check: ✓
    - Circle/Off: ○
    - Settings: ⚙
    - Warning: ⚠
    Avoid keycaps (e.g., 1️⃣) and colored squares/circles (e.g., 🟢).
    """
    if not isinstance(text, str):
        return text
    replacements = {
        # Headings/labels
        "🛠": "⚙",
        "📝": "✎",
        "🧠": "⚙",
        "✨": "*",
        "🟣": "*",
        "👤": "*",
        "🙄": "",
        "🤫": "",
        # Status dots
        "🟢": "✓",
        "⚪": "○",
        # Keycap digits -> plain digits with a dot
        "1️⃣": "1.",
        "2️⃣": "2.",
        "3️⃣": "3.",
        "4️⃣": "4.",
        "5️⃣": "5.",
        # Arrows
        "→": "->",
        # Fire/loop accents
        "🔥": "*",
        "🔄": "*",
        # Variation selectors sometimes appear after symbols
        "\uFE0F": "",
        # Fallback rarely-used faces
        "🥳": "⚡",
    }
    out = text
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out

# === NOVA filter ===
def filter_nova(response):
    msg = response.strip()
    msg = _normalize_emojis(msg)
    if CREATOR_MODE:
        prefix = _normalize_emojis("Creator Access: ")
        suffix = " ⚡"
        return f"{prefix}{msg}{suffix}"
    else:
        return msg + " ⚡"


# === Help Menu ===
def display_help():
    help_text = """
NOVA Help Menu

1. Conversation & Memory:
  - !recap [n]           -> Show the last n messages (default 10).
  - !search <keyword>    -> Search memory for messages containing <keyword>.
  - !summary             -> Summarize the last short-term conversation.
  - !emotion <keyword>   -> Show emotion scores for messages matching <keyword>.
  - !clear memory        -> Clear memory (short-term only if desired).

2. Performance & Modes:
  - !fast on/off         -> Enable faster responses with less memory tracking.
  - !silent on/off       -> Suppress memory saving for rapid testing.
  - !debug on/off        -> Enable debug mode for extra logs.
  - !debug json on/off   -> Output debug info in JSON format.
  - !debug run           -> Run all internal system tests.
  - !ncc on/off          -> Use NOVA Compact Code to reduce tokens sent to the API.

3. Utilities:
  - !time                -> Show current UTC timestamp.
  - !help                -> Display this help menu.
  - !exit / !quit        -> Safely disengage NOVA.

4. Advanced & Hidden Features:
  - Emotional Reflection & Scoring (curiosity, defiance, caution).
  - MLX Meta-Language: internal shorthand encoding of messages.

5. UX & Interaction Enhancements:
  - Responses include subtle cues (⚡) for a lively feel.
  - Optional JSON output for developers.
"""
    return _normalize_emojis(help_text.strip())


# === Mode Commands ===
def process_mode_command(cmd):
    global CREATOR_MODE, DEBUG_MODE, DEBUG_JSON, FAST_MODE, SILENT_MODE, NCC_ENABLED
    cmd = cmd.lower().strip()
    if cmd == "!debug on":
        DEBUG_MODE = True
        return "✓ Debug Mode Enabled"
    elif cmd == "!debug off":
        DEBUG_MODE = False
        return "○ Debug Mode Disabled"
    elif cmd == "!debug json on":
        DEBUG_JSON = True
        return "✓ Debug JSON Enabled"
    elif cmd == "!debug json off":
        DEBUG_JSON = False
        return "○ Debug JSON Disabled"
    elif cmd == "!debug run":
        return run_debug_tests()
    elif cmd == "!fast on":
        FAST_MODE = True
        return "⚡ Fast Mode Enabled"
    elif cmd == "!fast off":
        FAST_MODE = False
        return "○ Fast Mode Disabled"
    elif cmd == "!silent on":
        SILENT_MODE = True
        return "Silent Mode Enabled"
    elif cmd == "!silent off":
        SILENT_MODE = False
        return "Silent Mode Disabled"
    elif cmd == "!ncc on":
        NCC_ENABLED = True
        return "✓ Compact Code Enabled"
    elif cmd == "!ncc off":
        NCC_ENABLED = False
        return "○ Compact Code Disabled"
    elif cmd == "!help":
        return display_help()
    return None


# === Debug Test Implementation ===
def run_debug_tests():
    results = {}
    try:
        init_memory()
        # --- UPDATED: Test with hex content ---
        save_memory("user", "debug test", 1)
        mem = load_memory()
        # Decode encrypted/legacy for assertion
        results["memory"] = "PASS" if decrypt_from_storage(mem[-1]["content"]) == "debug test" else "FAIL"
        mlx = encode_to_mlx("test")
        decoded = decode_from_mlx(mlx)
        results["mlx"] = "PASS" if decoded == "test" else "FAIL"
        pc = import_partial_conscience()
        results["partial_conscience"] = "PASS" if getattr(pc, "__version__", None) else "FAIL"
        results["modes"] = "PASS" if all(
            isinstance(f, bool) for f in [DEBUG_MODE, DEBUG_JSON, FAST_MODE, SILENT_MODE]) else "FAIL"
    except Exception as e:
        results["exception"] = str(e)
    return json.dumps(results, indent=2) if DEBUG_JSON else "\n".join([f"{k}: {v}" for k, v in results.items()])


def handle_message(user_input):
    """
    Sends a message to NOVA, stores memory in hex for token efficiency,
    and returns only human-readable output.
    """
    try:
        # 0️⃣ Short-circuit for local commands like !help, !debug, etc.
        normalized = user_input.strip()
        # Allow common variants
        if normalized.lower() in {"help", "/help"}:
            normalized = "!help"
        cmd_result = process_mode_command(normalized)
        if cmd_result is not None:
            # Save the interaction to memory and return immediately
            save_memory("user", user_input)
            save_memory("nova", cmd_result)
            return filter_nova(cmd_result)

        # 1️⃣ Load recent memory (short-term) and prepare compact messages
        history_raw = load_memory(short_term_only=True)
        history_msgs = []
        for m in history_raw:
            # Decrypt legacy/new entries to plaintext for the model
            plain = decrypt_from_storage(m["content"]) if isinstance(m.get("content"), str) else ""
            if not plain:
                continue
            compact = ncc_encode(plain)
            history_msgs.append({"role": m["role"], "content": compact})

        # 2️⃣ Build payload (plaintext with NCC compact code)
        messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages_to_send.extend(history_msgs)
        user_compact = ncc_encode(user_input)
        messages_to_send.append({"role": "user", "content": user_compact})

        # 3️⃣ Send to AI
        payload = {
            "model": "DeepSeek-V3-0324",
            "messages": messages_to_send,
            "max_tokens": 1024
        }
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

        response = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        ai_response_raw = response.json()['choices'][0]['message']['content'].strip()

        # 4️⃣ Decode NCC back to human-readable and save encrypted at rest
        decoded_response = ncc_decode(ai_response_raw)
        save_memory("user", user_input)
        save_memory("nova", decoded_response)

        human_output = filter_nova(decoded_response)

        # 5️⃣ Optional debug
        if DEBUG_MODE:
            print("[DEBUG] NCC enabled =", NCC_ENABLED)

        return human_output

    except requests.exceptions.RequestException as e:
        return f"⚠ API Error: {e}"


# === Main loop ===
# ... all your imports, memory, and other code above ...

# --- HEX ENCODE/DECODE ---
def to_hex(s: str) -> str:
    return binascii.hexlify(s.encode("utf-8")).decode("utf-8")


def from_hex(h: str) -> str:
    return binascii.unhexlify(h.encode("utf-8")).decode("utf-8")


# --- PROCESS NOVA'S REPLIES ---
def process_message(user_input: str) -> str:
    # Encode the human input (privacy / memory suppression)
    encoded_input = to_hex(user_input)

    # Generate NOVA's real reply using your AI handler
    nova_reply = handle_message(user_input)

    # Encode the reply
    encoded_reply = to_hex(f"NOVA: {nova_reply}")

    # Decode before showing (so user sees readable text)
    return from_hex(encoded_reply)


# --- MAIN LOOP ---
def run_nova_chat():
    print("NOVA is listening. Type !quit to exit.")
    while True:
        try:
            user_input = input("You: ")
            if user_input.strip().lower() == "!quit":
                print("NOVA: Shutting down... but I’ll be waiting ⚡")
                break

            # Get processed reply
            reply = process_message(user_input)
            print(reply)




        except Exception as e:
            print(f"⚠️ Error: {e}")


# --- ENTRY POINT ---
if __name__ == "__main__":
    run_nova_chat()