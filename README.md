# WhatsApp Chat Bot

A WhatsApp chatbot powered by Twilio and OpenAI, specialized in data engineering expertise. The bot maintains conversation context and provides concise, expert answers.

## Features

- **WhatsApp Integration**: Receive and respond to WhatsApp messages via Twilio
- **OpenAI GPT Models**: Uses OpenAI's GPT models (gpt-4o-mini default) for intelligent responses
- **Conversation Memory**: Maintains conversation history per user (in-memory)
- **Session Management**: Automatic session timeout and cleanup
- **Data Engineering Expert**: Specialized system prompt for data engineering topics
- **Special Commands**: Users can type "clear", "reset", or "start over" to reset conversation
- **Health Monitoring**: Built-in health check and statistics endpoints

## Project Structure

```
twilio-whatsapp/
├── app.py                              # FastAPI application with Twilio webhooks
├── config/
│   ├── settings.py                     # Configuration management
│   └── prompts.py                      # System prompts for LLM
├── services/
│   ├── llm_service.py                  # OpenAI integration
│   └── conversation_manager.py         # Session and history management
├── .env.example                        # Environment variables template
└── pyproject.toml                      # Project dependencies
```

## Setup

### 1. Prerequisites

- Python 3.12+
- Twilio account with WhatsApp sandbox enabled
- OpenAI API key

### 2. Installation

```bash
# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Twilio (from https://console.twilio.com/)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# OpenAI (from https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini
```

**Available OpenAI Models:**

- `gpt-4o-mini` - Recommended, cost-effective, fast
- `gpt-4o` - Most capable, higher cost
- `gpt-4-turbo` - Balanced performance
- `gpt-3.5-turbo` - Cheapest option

### 4. Twilio WhatsApp Setup

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to Messaging > Try it out > Send a WhatsApp message
3. Join the sandbox by sending the code to the Twilio WhatsApp number
4. Configure webhook URL (see Running section below)

## Running

### Local Development

```bash
# Run with FastAPI development server
fastapi dev app.py

# Or with uvicorn directly
uvicorn app:app --reload --port 8000
```

### Expose Local Server (for Twilio webhook)

Use ngrok or similar tool to expose your local server:

```bash
ngrok http 8000
```

Then configure the ngrok URL in Twilio Console:

- Webhook URL: `https://your-ngrok-url.ngrok.io/chat/whatsapp`
- Method: POST

### Production

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Webhook Endpoint

- **POST** `/chat/whatsapp` - Receives WhatsApp messages from Twilio

### Utility Endpoints

- **GET** `/` - API information
- **GET** `/health` - Health check
- **GET** `/stats` - Conversation statistics
- **POST** `/send-message` - Send outbound WhatsApp message

### Example: Send Message

```bash
curl -X POST "http://localhost:8000/send-message?phone_number=+1234567890&message=Hello"
```

#### Via whatsapp

1. Open a WhatsApp chat with your Twilio number
2. Send a message like "Hello, What is Apache Spark?"

## Usage

1. Start the server
2. Send a WhatsApp message to your Twilio number
3. The bot responds with data engineering expertise
4. Conversation context is maintained across messages
5. Type "clear" to reset the conversation

### Example Conversation

```
User: What is Apache Spark?
Bot: Apache Spark is a unified analytics engine for large-scale data processing.
     It provides high-level APIs in Python, Java, Scala, and R, plus an optimized
     engine supporting general computation graphs. Used for batch processing,
     streaming, ML, and graph processing.

User: How does it differ from Hadoop?
Bot: Key differences:
     • Speed: Spark is 100x faster (in-memory) than Hadoop MapReduce
     • Ease: Higher-level APIs vs verbose MapReduce code
     • Real-time: Spark supports streaming; Hadoop is batch-only
     • Flexibility: Spark runs on Hadoop YARN, standalone, or Kubernetes
```

## Configuration Options

Edit [config/settings.py](config/settings.py) or set environment variables:

- `OPENAI_MODEL` (default: gpt-4o-mini) - OpenAI model to use
- `LLM_TEMPERATURE` (default: 0.3) - Response randomness (0-1)
- `LLM_MAX_TOKENS` (default: 500) - Max response length
- `MAX_CONVERSATION_HISTORY` (default: 10) - Messages to remember
- `SESSION_TIMEOUT_MINUTES` (default: 30) - Session expiry time

## Database (Optional/Persistent)

If you want persistent conversation history, use the PostgreSQL backend and follow the database setup guide:

- Start PostgreSQL with Docker: `docker-compose up -d`
- Setup guide: [database/README.md](database/README.md)
- Set `STORAGE_BACKEND=database` in your `.env` and configure `POSTGRES_*` values

## Customization

### Change System Prompt

Edit [config/prompts.py](config/prompts.py) to customize the bot's personality and expertise.

### Adjust Conversation Memory

Modify settings in [config/settings.py](config/settings.py) or use environment variables.

### Switch Models

Change `OPENAI_MODEL` in your `.env` file to use a different GPT model.

## Troubleshooting

**Bot not responding:**

- Check Twilio webhook is configured correctly
- Verify server is accessible (use ngrok for local dev)
- Check logs for errors

**Invalid API key errors:**

- Verify OPENAI_API_KEY in .env file
- Ensure API key has proper permissions
- Check you have credits in your OpenAI account

**Session issues:**

- Sessions reset on server restart (in-memory storage)
- Check SESSION_TIMEOUT_MINUTES setting

**Rate limit errors:**

- OpenAI has rate limits based on your tier
- Consider upgrading your OpenAI plan
- Or switch to gpt-3.5-turbo for higher limits

## Development

```bash
# Format code
black .

# Type checking
mypy .

# Linting
ruff check .
```
