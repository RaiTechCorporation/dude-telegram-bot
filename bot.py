import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import os
import threading
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# ==============================================================================
# CONFIGURATION & LINKS
# ==============================================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8345049769:AAGpuJK0RNAARREQRfrUNy8V4wLLNNrhr1A")
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL", "@dudedex")
TELEGRAM_CHANNEL_LINK = "https://t.me/dudedex"
WHATSAPP_CHANNEL_LINK = "https://whatsapp.com/channel/0029Vb7njM26GcGIDj2Lib37"
YOUTUBE_CHANNEL_LINK = "https://www.youtube.com/@DudeDex"
APP_DOWNLOAD_LINK = "https://dudedex.cloud/app/D-DEX.apk"
WEB_APP_LINK = "https://wallet.dudedex.cloud/"

# Delay between task steps (in seconds)
DELAY_SECONDS = int(os.environ.get("DELAY_SECONDS", "15"))

# Image Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WELCOME_IMAGE_PATH = os.path.join(BASE_DIR, "images", "welcome.jpeg")
REWARD_IMAGE_PATH = os.path.join(BASE_DIR, "images", "reward.jpg")

# ==============================================================================
# LOGGING SETUP
# ==============================================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ==============================================================================
# HEALTH CHECK SERVER (FOR CLOUD DEPLOYMENTS / RENDER)
# ==============================================================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - DUDE DEX Telegram Bot is running")

    def log_message(self, format, *args):
        return  # Suppress noisy HTTP logs


def start_health_server() -> None:
    port = int(os.environ.get("PORT", "8080"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Health check server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Could not start health check server: {e}")



# ==============================================================================
# CHANNEL MEMBERSHIP VERIFICATION
# ==============================================================================
async def check_channel_member(bot, user_id: int, channel_id: str) -> bool:
    """
    Verifies if the user is currently a member/admin/owner of the Telegram channel.
    Requires the bot to be an Administrator in the channel.
    """
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        valid_statuses = {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
            "member",
            "administrator",
            "creator",
        }
        if member.status in valid_statuses:
            return True
        if member.status == ChatMemberStatus.RESTRICTED and getattr(member, "is_member", True):
            return True
        return False
    except BadRequest as e:
        logger.warning(f"BadRequest checking member {user_id} in {channel_id}: {e}")
        return False
    except TelegramError as e:
        logger.error(f"TelegramError checking member {user_id} in {channel_id}: {e}")
        return False


# ==============================================================================
# COMMAND HANDLER: /start
# ==============================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles /start command: sends the high-converting welcome message & Step 1 buttons.
    """
    welcome_text = (
        "🔥 <b>Welcome to the DUDE DEX Official Airdrop!</b> 🎁\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>The All-in-One Web3 Ecosystem on BNB Smart Chain</i>\n\n"
        "💎 <b>Complete simple tasks & claim your $5 Free Asset instantly!</b>\n"
        "Use your asset for <b>P2P Trading</b>, <b>Token Swaps</b>, <b>Staking Yields</b> &amp; <b>Web3 Games</b>.\n\n"
        "⚠️ <b>Step 1 is mandatory:</b> You must join our official Telegram channel first.\n\n"
        "📢 <b>Step 1 — Join Official Telegram Channel</b>\n"
        "Stay updated with live announcements, token listings &amp; platform rewards.\n\n"
        "👇 <b>Click the buttons below to begin:</b>"
    )

    keyboard = [
        [
            InlineKeyboardButton("📢 JOIN TELEGRAM CHANNEL", url=TELEGRAM_CHANNEL_LINK)
        ],
        [
            InlineKeyboardButton("✅ VERIFY TELEGRAM JOIN", callback_data="verify_tg")
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id

    # If welcome banner image exists, send it with styled caption
    if os.path.exists(WELCOME_IMAGE_PATH):
        try:
            with open(WELCOME_IMAGE_PATH, "rb") as photo_file:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=welcome_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                )
                return
        except Exception as e:
            logger.warning(f"Could not send photo, falling back to text: {e}")

    # Fallback to text message
    if update.message:
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )


# ==============================================================================
# CALLBACK QUERY HANDLER
# ==============================================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles interactive inline button clicks with rich styling.
    """
    query = update.callback_query
    if not query:
        return

    data = query.data
    user = query.from_user
    chat_id = query.message.chat_id if query.message else user.id

    # --------------------------------------------------------------------------
    # Step 1: Verify Telegram Join
    # --------------------------------------------------------------------------
    if data == "verify_tg":
        is_member = await check_channel_member(context.bot, user.id, TELEGRAM_CHANNEL)

        if not is_member:
            await query.answer(
                "❌ Verification Failed!\nPlease join @dudedex channel first before verifying.",
                show_alert=True,
            )
            return

        # Acknowledge button click
        await query.answer("✅ Channel Verified Successfully!")

        # Step 2 Message
        step2_text = (
            "✅ <b>Step 1 Verified!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💬 <b>Step 2 — Join WhatsApp VIP Channel</b>\n\n"
            "Get early access to:\n"
            "• 🚀 New Token Listings &amp; Swap Rates\n"
            "• 📈 High APY Staking Pools\n"
            "• 🎁 Exclusive Community Giveaways\n\n"
            "👇 <b>Click below to join our WhatsApp channel:</b>"
        )
        step2_keyboard = [
            [
                InlineKeyboardButton("▶️ Join WhatsApp Channel", url=WHATSAPP_CHANNEL_LINK)
            ]
        ]
        
        try:
            if query.message.photo:
                await query.edit_message_caption(
                    caption=step2_text,
                    reply_markup=InlineKeyboardMarkup(step2_keyboard),
                    parse_mode=ParseMode.HTML,
                )
            else:
                await query.edit_message_text(
                    text=step2_text,
                    reply_markup=InlineKeyboardMarkup(step2_keyboard),
                    parse_mode=ParseMode.HTML,
                )
        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text=step2_text,
                reply_markup=InlineKeyboardMarkup(step2_keyboard),
                parse_mode=ParseMode.HTML,
            )

        # Wait exactly 15 seconds
        await asyncio.sleep(DELAY_SECONDS)

        # Send confirmation button for Step 2
        confirm_wa_keyboard = [
            [
                InlineKeyboardButton("✅ I have joined", callback_data="joined_whatsapp")
            ]
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⏳ <b>Step 2 Confirmation</b>\n\n"
                "Have you joined our WhatsApp channel? Click below to proceed to the final step:"
            ),
            reply_markup=InlineKeyboardMarkup(confirm_wa_keyboard),
            parse_mode=ParseMode.HTML,
        )

    # --------------------------------------------------------------------------
    # Step 2: WhatsApp Confirmed -> Step 3 YouTube
    # --------------------------------------------------------------------------
    elif data == "joined_whatsapp":
        await query.answer("Step 2 Completed!")

        step3_text = (
            "✅ <b>Step 2 Verified!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📱 <b>Step 3 — Subscribe to Official YouTube Channel</b>\n\n"
            "Watch tutorials on:\n"
            "• 💳 How to setup &amp; use the D-DEX Web3 Wallet\n"
            "• 🔄 Mastering P2P DEX Trading &amp; Token Swaps\n"
            "• 🎮 Playing Web3 Games &amp; Staking for Passive Income\n\n"
            "👇 <b>Click below to subscribe:</b>"
        )
        step3_keyboard = [
            [
                InlineKeyboardButton("▶️ Subscribe YouTube", url=YOUTUBE_CHANNEL_LINK)
            ]
        ]

        if query.message:
            try:
                if query.message.photo:
                    await query.edit_message_caption(
                        caption=step3_text,
                        reply_markup=InlineKeyboardMarkup(step3_keyboard),
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await query.edit_message_text(
                        text=step3_text,
                        reply_markup=InlineKeyboardMarkup(step3_keyboard),
                        parse_mode=ParseMode.HTML,
                    )
            except Exception:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=step3_text,
                    reply_markup=InlineKeyboardMarkup(step3_keyboard),
                    parse_mode=ParseMode.HTML,
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=step3_text,
                reply_markup=InlineKeyboardMarkup(step3_keyboard),
                parse_mode=ParseMode.HTML,
            )

        # Wait exactly 15 seconds
        await asyncio.sleep(DELAY_SECONDS)

        # Send confirmation button for Step 3
        confirm_yt_keyboard = [
            [
                InlineKeyboardButton("✅ I have subscribed", callback_data="subscribed_youtube")
            ]
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "⏳ <b>Step 3 Confirmation</b>\n\n"
                "Have you subscribed to our YouTube channel? Click below to claim your <b>$5 Airdrop Asset</b>:"
            ),
            reply_markup=InlineKeyboardMarkup(confirm_yt_keyboard),
            parse_mode=ParseMode.HTML,
        )

    # --------------------------------------------------------------------------
    # Step 3: YouTube Confirmed -> Final Reward Banner & Detailed Platform Guide
    # --------------------------------------------------------------------------
    elif data == "subscribed_youtube":
        await query.answer("🎉 Congratulations! All tasks completed!")

        congrats_text = (
            "🎉 <b>CONGRATULATIONS! ALL TASKS COMPLETED!</b> 🏆\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💰 <b>Your $5 Free Crypto Asset is Ready to Claim!</b>\n\n"
            "Explore the full power of <b>D-DEX (BNB Chain)</b>:\n"
            "• 💳 <b>Web3 Wallet</b> — Fast BNB Smart Chain deposits &amp; withdrawals\n"
            "• 🔄 <b>P2P DEX &amp; Token Swap</b> — Direct decentralized trading\n"
            "• 📈 <b>Staking Vaults</b> — Earn high APY crypto rewards\n"
            "• 🎮 <b>Web3 Games</b> — Play, compete &amp; win crypto\n"
            "• 👥 <b>Referral Program</b> — Earn commissions with your team\n\n"
            "👇 <b>Download the App or Launch Web Wallet now:</b>"
        )
        reward_keyboard = [
            [
                InlineKeyboardButton("📱 Download Android App", url=APP_DOWNLOAD_LINK),
                InlineKeyboardButton("🌐 Launch Web Wallet", url=WEB_APP_LINK),
            ]
        ]

        # Send Congratulations with reward photo if available
        if os.path.exists(REWARD_IMAGE_PATH):
            try:
                with open(REWARD_IMAGE_PATH, "rb") as photo_file:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file,
                        caption=congrats_text,
                        reply_markup=InlineKeyboardMarkup(reward_keyboard),
                        parse_mode=ParseMode.HTML,
                    )
            except Exception as e:
                logger.warning(f"Could not send reward photo, fallback to text: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=congrats_text,
                    reply_markup=InlineKeyboardMarkup(reward_keyboard),
                    parse_mode=ParseMode.HTML,
                )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=congrats_text,
                reply_markup=InlineKeyboardMarkup(reward_keyboard),
                parse_mode=ParseMode.HTML,
            )

        # Send detailed, visually formatted claim guide
        guide_text = (
            "📖 <b>EASY GUIDE: HOW TO CLAIM &amp; USE YOUR $5 ASSET</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣ <b>Install &amp; Open:</b> Download the D-DEX APK or launch the Web Wallet.\n"
            "2️⃣ <b>Create / Connect:</b> Set up your Web3 wallet securely (BNB Smart Chain).\n"
            "3️⃣ <b>Claim Reward:</b> Go to the <b>Rewards / Airdrop</b> section.\n"
            "4️⃣ <b>Instant Credit:</b> Your $5 reward balance activates immediately!\n"
            "5️⃣ <b>Play, Trade &amp; Withdraw:</b> Use your balance for P2P trades, token swaps, staking yields, or Web3 games.\n\n"
            "🔒 <b>Security Reminder:</b> Never share your wallet seed phrase or private key with anyone. D-DEX will never ask for your recovery phrase."
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=guide_text,
            parse_mode=ParseMode.HTML,
        )


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main() -> None:
    """
    Initializes and starts the Telegram Bot application.
    """
    logger.info("Starting DUDE DEX Airdrop Bot with enhanced rich styling...")

    # Start health check server for cloud hosting / Render
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    application = Application.builder().token(BOT_TOKEN).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Run the bot with polling
    logger.info("Bot is running and polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
