# Telegram Voice Message Downloader

A TypeScript Node.js application that downloads voice messages from specified Telegram chats using the MTProto API.

## Prerequisites

- Node.js (v14 or higher)
- npm
- Telegram API credentials (API ID and API Hash)

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the root directory with the following content:
   ```
   API_ID=your_api_id
   API_HASH=your_api_hash
   PHONE_NUMBER=your_phone_number
   TARGET_CHAT_IDS=chat_id1,chat_id2
   ```

   To get your API credentials:
   1. Visit https://my.telegram.org/auth
   2. Log in with your phone number
   3. Go to 'API development tools'
   4. Create a new application
   5. Copy the API ID and API Hash

## Usage

1. Build the project:
   ```bash
   npm run build
   ```

2. Run the application:
   ```bash
   npm start
   ```

   Or for development:
   ```bash
   npm run dev
   ```

The application will:
1. Connect to Telegram
2. Process each specified chat
3. Download all voice messages
4. Save them in the `downloads/<chat_id>` directory

## Project Structure

- `src/`
  - `index.ts` - Main entry point
  - `config.ts` - Configuration and environment variables
  - `telegramClient.ts` - Telegram MTProto client implementation
  - `types/` - TypeScript type definitions

## Notes

- Voice messages are saved in OGG format
- Files are named `voice_<message_id>.ogg`
- The application creates a separate directory for each chat's downloads 