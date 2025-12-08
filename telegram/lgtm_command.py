import os
import re
import logging
import requests
from typing import Optional, Tuple
import telegram
from telegram import Update
from telegram.ext import (
    Application, 
    ContextTypes, 
    CommandHandler 
)

# Telegram and GitHub Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GITHUB_MERGE_TOKEN = os.getenv("GITHUB_MERGE_TOKEN")
WORKFLOW_FILE_NAME = "merge-by-telegram.yml"

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def extract_pr_info(message_text: str) -> Optional[Tuple[str, int]]:
    """
    Extracts the GitHub repository name and the simple PR Number 
    from a multiline notification message.
    """
    repo_pattern = re.compile(r'Repository:\s+(\S+)', re.IGNORECASE)
    pr_number_pattern = re.compile(r'PR_id:\s+(\d+)', re.IGNORECASE)

    repo_match = repo_pattern.search(message_text)
    pr_number_match = pr_number_pattern.search(message_text)

    if repo_match and pr_number_match:
        repository_name = repo_match.group(1).strip()
        pr_number = int(pr_number_match.group(1))
        
        return repository_name, pr_number
    else:
        logger.warning(f"Failed to extract repo or PR Number from message: \n{message_text}")
        return None

# --- GITHUB API HANDLER (Synchronous) ---
def dispatch_github_workflow(repository_name: str, pr_number: int):
    """Triggers the GitHub workflow_dispatch API to merge the PR."""
    
    # Use the repository name provided by the user
    url = (
        f"https://api.github.com/repos/{repository_name}/"
        f"actions/workflows/{WORKFLOW_FILE_NAME}/dispatches"
    )
    
    headers = {
        "Authorization": f"token {GITHUB_MERGE_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    payload = {
        "ref": "main", 
        "inputs": {
            "pr_number": str(pr_number)
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        logger.info(f"Successfully dispatched workflow for PR #{pr_number} on {repository_name}. Status: {response.status_code}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"Failed to dispatch workflow for PR #{pr_number}. Error: {e}, Response: {response.text}")
        return False


# --- COMMAND HANDLERS (Asynchronous) ---
async def handle_lgtm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /lgtm command. If it's a reply to a bot message, it extracts 
    PR info from the replied message text.
    """

    logger.info("RECEIVED /LGTM COMMAND. Processing...")

    chat_id = update.effective_chat.id
    pr_info = None

    # 1. Check if the message is a reply
    replied_message = update.message.reply_to_message
    
    if replied_message and replied_message.text:
        logger.info("Command is a reply. Attempting to parse replied message text.")
        
        # Use the text from the replied message
        pr_info = extract_pr_info(replied_message.text)
        
    elif context.args and len(context.args) == 2:
        # 2. Fallback: If not a reply, check for explicit arguments (for flexibility)
        logger.info("Command is not a reply. Using explicit arguments.")
        repository_name = context.args[0].strip()
        pr_number_str = context.args[1].strip()
        
        try:
            pr_number = int(pr_number_str)
            pr_info = (repository_name, pr_number)
        except ValueError:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ **Error:** PR number must be an integer. Received: `{pr_number_str}`",
                parse_mode='Markdown'
            )
            return
            
    else:
        # 3. Handle incorrect usage
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ **Usage Error:** Command must either:\n1. Reply to a PR notification.\n2. Use the format `/lgtm <owner/repo> <pr_number>`.",
            parse_mode='Markdown'
        )
        return
    
    # --- Proceed with Dispatch ---
    if pr_info:
        repository_name, pr_number = pr_info
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🤖 Attempting merge of PR #{pr_number} in `{repository_name}` via reply...",
            parse_mode='Markdown'
        )
        
        success = dispatch_github_workflow(repository_name, pr_number)

        if success:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ **Merge Approved!** Workflow triggered successfully for PR #{pr_number}.",
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ **Merge Failed!** GitHub API call failed. Check bot logs.",
                parse_mode='Markdown'
            )

# --- TEST HANDLER ---
async def send_test_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a predefined test PR message when the /testmerge command is used."""
    
    logger.info("RECEIVED /TESTMERGE COMMAND. Processing...")
    
    # Use the current chat ID
    chat_id = update.effective_chat.id 
    
    # Define test variables (must match the expected format)
    TEST_PR_NUMBER = 14
    TEST_REPO = "cattias/kikinodeapp"
    
    TEST_MESSAGE_TEXT = """
1️⃣ __KikiServer__: New Renovate PR""" + telegram.helpers.escape_markdown(f"""
Repository: {TEST_REPO}
Title: chore(deps): update test-app to v9.9.9
URL: https://github.com/{TEST_REPO}/pull/{TEST_PR_NUMBER}
PR_id: {TEST_PR_NUMBER} 
""", version=2)
    
    # 1. Send the message
    await context.bot.send_message(
        chat_id=chat_id,
        text=TEST_MESSAGE_TEXT,
        parse_mode='MarkdownV2'
    )

# --- 4. MAIN EXECUTION ---

def main() -> None:
    """Start the single bot application."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Missing TELEGRAM_BOT_TOKEN.")
        return

    # 1. Build the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 2. Register Handlers
    # CRITICAL: pass_args=True allows the handler to receive the text arguments
    application.add_handler(CommandHandler("lgtm", handle_lgtm_command))
    application.add_handler(CommandHandler("testmerge", send_test_message))
    
    logger.info("Bot application initialized and handlers registered.")

    # 3. Run the bot using synchronous polling
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")

if __name__ == "__main__":
    main()