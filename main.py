import os
import logging
import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from gtts import gTTS
import openai
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure API keys
TELEGRAM_API_KEY = "YOUR_TELEGRAM_API_KEY"
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Configure AI Models
genai.configure(api_key=GOOGLE_API_KEY)
openai.api_key = OPENAI_API_KEY

# Initialize models
gemini_pro = genai.GenerativeModel('gemini-pro')
gemini_vision = genai.GenerativeModel('gemini-pro-vision')

# User preferences storage
user_preferences = {}

# Model selection keyboard
model_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Gemini", callback_data="model_gemini"),
        InlineKeyboardButton("GPT-4", callback_data="model_gpt4")
    ],
    [
        InlineKeyboardButton("Image Generation", callback_data="image_gen"),
        InlineKeyboardButton("Voice Mode", callback_data="voice_mode")
    ]
])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced start command with welcome message and model selection."""
    user_id = update.effective_user.id
    user_preferences[user_id] = {
        'model': 'gemini',
        'voice_mode': False,
        'conversation_history': []
    }
    
    welcome_message = (
        "🤖 Welcome to Enhanced AI Assistant!\n Developed by thrid year SE Students, ASTU!\n\n"
        "Features available:\n"
        "🗣️ Multi-model conversation (Gemini & GPT-4)\n"
        "🎨 Image generation\n"
        "🗣️ Voice messages\n"
        "📸 Image analysis\n"
        "🔄 Conversation memory\n\n"
        "Commands:\n"
        "/start - Restart bot\n"
        "/help - Show help\n"
        "/clear - Clear history\n"
        "/settings - Change preferences\n"
        "/model - Switch AI model\n"
        "/image - Generate image\n"
        "/voice - Toggle voice mode\n\n"
        "Please select your preferred model:"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=model_keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced help command with detailed feature explanation."""
    help_message = (
        "🤖 Enhanced AI Assistant Help\n\n"
        "Basic Commands:\n"
        "/start - Initialize or restart the bot\n"
        "/help - Show this help message\n"
        "/clear - Clear conversation history\n"
        "/settings - Adjust your preferences\n"
        "/model - Switch between AI models\n"
        "/image - Generate images\n"
        "/voice - Toggle voice responses\n\n"
        "Features:\n"
        "🤖 Multi-Model Chat: Switch between Gemini and GPT-4\n"
        "🎨 Image Generation: Create images from descriptions\n"
        "🗣️ Voice Mode: Receive voice responses\n"
        "📸 Image Analysis: Send images for AI analysis\n"
        "💭 Memory: Bot remembers conversation context\n\n"
        "Tips:\n"
        "- Send images for analysis\n"
        "- Use 'Generate image:' prefix for image creation\n"
        "- Toggle voice mode for audio responses"
    )
    await update.message.reply_text(help_message)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings command to adjust user preferences."""
    user_id = update.effective_user.id
    current_settings = user_preferences.get(user_id, {
        'model': 'gemini',
        'voice_mode': False
    })
    
    settings_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"Model: {current_settings.get('model', 'gemini').upper()}",
            callback_data="change_model"
        )],
        [InlineKeyboardButton(
            f"Voice Mode: {'ON' if current_settings.get('voice_mode', False) else 'OFF'}",
            callback_data="toggle_voice"
        )]
    ])
    
    await update.message.reply_text(
        "⚙️ Settings\nCustomize your AI Assistant:",
        reply_markup=settings_keyboard
    )

async def generate_image(prompt: str) -> bytes:
    """Generate image using DALL-E."""
    try:
        response = await openai.Image.acreate(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        # Download and return image bytes
        # Implementation depends on your HTTP client
        return image_url
    except Exception as e:
        logger.error(f"Image generation error: {str(e)}")
        raise

async def text_to_speech(text: str) -> str:
    """Convert text to speech and return file path."""
    try:
        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
        raise

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if query.data.startswith("model_"):
        model = query.data.split("_")[1]
        user_preferences[user_id]['model'] = model
        await query.message.edit_text(f"Model switched to {model.upper()}")
    
    elif query.data == "voice_mode":
        current_mode = user_preferences[user_id].get('voice_mode', False)
        user_preferences[user_id]['voice_mode'] = not current_mode
        await query.message.edit_text(
            f"Voice mode {'enabled' if not current_mode else 'disabled'}"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced message handler with multiple models and features."""
    user_id = update.effective_user.id
    message = update.message
    
    if not user_id in user_preferences:
        user_preferences[user_id] = {
            'model': 'gemini',
            'voice_mode': False,
            'conversation_history': []
        }
    
    try:
        await update.message.chat.send_action(action="typing")
        
        # Handle image messages
        if message.photo:
            image_file = await message.photo[-1].get_file()
            # Process image with Gemini Vision
            response = await process_image(image_file)
            await send_response(update, context, response)
            return
        
        # Handle text messages
        text = message.text
        
        # Handle image generation requests
        if text.lower().startswith("generate image:"):
            prompt = text[len("generate image:"):].strip()
            image_url = await generate_image(prompt)
            await message.reply_photo(image_url, caption="Generated image based on your prompt")
            return
        
        # Normal text processing
        model = user_preferences[user_id]['model']
        if model == 'gemini':
            response = await process_with_gemini(text)
        else:  # GPT-4
            response = await process_with_gpt4(text)
        
        # Store in conversation history
        user_preferences[user_id]['conversation_history'].append({
            'role': 'user',
            'content': text
        })
        user_preferences[user_id]['conversation_history'].append({
            'role': 'assistant',
            'content': response
        })
        
        await send_response(update, context, response)
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await update.message.reply_text(
            "Sorry, I encountered an error. Please try again."
        )

async def process_image(image_file):
    """Process image with Gemini Vision."""
    try:
        image_bytes = await image_file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes))
        response = gemini_vision.generate_content(image)
        return response.text
    except Exception as e:
        logger.error(f"Image processing error: {str(e)}")
        raise

async def process_with_gemini(text: str) -> str:
    """Process text with Gemini model."""
    response = gemini_pro.generate_content(text)
    return response.text

async def process_with_gpt4(text: str) -> str:
    """Process text with GPT-4 model."""
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": text}]
    )
    return response.choices[0].message.content

async def send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Send response with optional voice."""
    user_id = update.effective_user.id
    voice_mode = user_preferences[user_id].get('voice_mode', False)
    
    # Split long messages
    max_length = 4000
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    
    for chunk in chunks:
        await update.message.reply_text(chunk)
        
        if voice_mode:
            voice_file = await text_to_speech(chunk)
            await update.message.reply_voice(voice_file)
            os.unlink(voice_file)  # Clean up temporary file

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text(
            "Sorry, an error occurred. Please try again later."
        )
    except:
        pass

def main():
    """Start the enhanced bot."""
    application = Application.builder().token(TELEGRAM_API_KEY).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(
        filters.PHOTO | filters.TEXT & ~filters.COMMAND,
        handle_message
    ))
    application.add_error_handler(error_handler)

    print("Starting enhanced bot...")
    application.run_polling()

if __name__ == "__main__":
    main()