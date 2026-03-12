import { TelegramClient } from "telegram";
import { StringSession } from "telegram/sessions";
import { config } from "./config";

async function main() {
  try {
    // Create a new Telegram client
    const client = new TelegramClient(
      new StringSession(config.sessionString || ""),
      config.apiId,
      config.apiHash,
      { connectionRetries: 5 }
    );

    // Login (will use saved session if available)
    await client.start({
      phoneNumber: () => Promise.resolve(config.phoneNumber),
      password: () => Promise.resolve(config.password || ""),
      phoneCode: async () => {
        console.log("Please enter the code you received:");
        return new Promise((resolve) => {
          process.stdin.once("data", (data) => {
            resolve(data.toString().trim());
          });
        });
      },
      onError: (err) => console.error("Login error:", err),
    });

    // Save the session string for future use
    console.log("Session string:", client.session.save());

    const chatsIds = {
      berghain: -1001234400699,
    };

    // Get last message from the configured chat
    const messages = await client.getMessages(chatsIds.berghain, {
      limit: 100,
      offsetDate: 1758449670,
    });

    console.log(messages.length);

    messages.forEach((message) => {
      console.log(message.date, message.message);
    });
  } catch (error) {
    console.error("Error:", error);
  }
}

// Start the application
main();
