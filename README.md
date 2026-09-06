# DUDE DEX Airdrop Telegram Bot

A complete, lightweight Telegram Bot for the **DUDE DEX Airdrop Campaign** built using `python-telegram-bot` (version 20+ async).

> **Stateless Design:** No database, JSON file, or external storage is required. Everything runs purely within Telegram using messages, inline buttons, and callback queries.

---

## 📋 Bot Flow

1. **/start**:
   - Sends the official welcome message.
   - Shows buttons:
     - 📢 `JOIN TELEGRAM CHANNEL` (URL)
     - ✅ `VERIFY TELEGRAM JOIN` (Callback)

2. **Step 1 Verification**:
   - Checks membership in `@dudedex` via `get_chat_member`.
   - If not joined: Shows alert popup `"Please join the channel first"`.
   - If joined: Edits message to **Step 2 — Join WhatsApp Channel** with `▶️ Join WhatsApp Channel` button.
   - Waits **15 seconds** (`asyncio.sleep(15)`), then sends a new message with button `✅ I have joined`.

3. **Step 2 Confirmation & Step 3**:
   - When user clicks `✅ I have joined`, shows **Step 3 — Subscribe to YouTube Channel** with button `▶️ Subscribe YouTube`.
   - Waits **15 seconds** (`asyncio.sleep(15)`), then sends a new message with button `✅ I have subscribed`.

4. **Step 3 Confirmation & Final Reward**:
   - When user clicks `✅ I have subscribed`, sends the final congratulatory message with:
     - 📱 `Download App`
     - 🌐 `Use with Web`
   - Sends the step-by-step airdrop claim guide.

---

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Make Bot Admin in Channel
Ensure the bot is added as an **Administrator** in `@dudedex` so it can check channel membership.

### 3. Run the Bot
```bash
python3 bot.py
```
