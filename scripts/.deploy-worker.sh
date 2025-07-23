# TODO
# publish mac mini on internet, only ssh port
# create ssh key and use it to connect from here
# make this file work

#!/bin/bash

# === CONFIGURE THIS ===
MAC_USER="your_mac_mini_username"
MAC_HOST="your.macmini.public.ip"     # Or a DNS name
PROJECT_DIR="/Users/$MAC_USER/light-llm-api"
GIT_REPO="https://github.com/marcostevanon/light-llm-api.git"
PYTHON_PATH="/usr/bin/python3"         # Adjust if using pyenv/homebrew
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="$PROJECT_DIR/app.log"
PORT=8000

echo "🔗 Connecting to $MAC_HOST..."

ssh "$MAC_USER@$MAC_HOST" bash -s <<EOF
  echo "📁 Setting up project..."
  if [ ! -d "$PROJECT_DIR" ]; then
    git clone $GIT_REPO $PROJECT_DIR
  fi

  cd "$PROJECT_DIR"
  echo "🔄 Pulling latest changes..."
  git pull

  echo "🐍 Setting up virtualenv..."
  if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_PATH -m venv venv
  fi

  source "$VENV_DIR/bin/activate"
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt

  echo "🚀 Starting FastAPI app on port $PORT..."
  pkill -f "uvicorn main:app" || true  # Kill old process if running
  nohup uvicorn main:app --host 0.0.0.0 --port $PORT > "$LOG_FILE" 2>&1 &
  echo "✅ App running at http://$MAC_HOST:$PORT"

EOF
