#!/bin/bash

# Define variables
REPO_URL="https://github.com/s-b-repo/worldroute.git"  # Update with your repository URL
TOOL_NAME="world.rs"  # Name of your Rust tool
INSTALL_DIR="$HOME/$TOOL_NAME"

# Check for existing Rust installation
if ! command -v rustc &> /dev/null
then
    echo "[INFO] Rust is not installed. Installing Rust using rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo "[INFO] Rust is already installed."
fi

# Ensure Cargo is in PATH
if ! command -v cargo &> /dev/null
then
    echo "[ERROR] Cargo was not found in PATH. Please add it and try again."
    exit 1
fi

# Install dependencies
echo "[INFO] Installing required dependencies..."
cargo install csv tokio futures serde serde_derive serde_json  # Add any other dependencies

# Clone or copy the repository
if [ -d "$INSTALL_DIR" ]; then
    echo "[INFO] Directory $INSTALL_DIR already exists. Pulling latest changes..."
    git -C "$INSTALL_DIR" pull
else
    echo "[INFO] Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

# Navigate to the project directory
cd "$INSTALL_DIR" || { echo "[ERROR] Could not navigate to $INSTALL_DIR"; exit 1; }

# Build the project
echo "[INFO] Building the Rust project..."
cargo build --release

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "[ERROR] Build failed. Please check the output for errors."
    exit 1
fi

# Add the executable to PATH
EXECUTABLE_PATH="$INSTALL_DIR/target/release/$TOOL_NAME"
if [ -f "$EXECUTABLE_PATH" ]; then
    echo "[INFO] Adding $EXECUTABLE_PATH to PATH..."
    echo "export PATH=\"\$PATH:$INSTALL_DIR/target/release\"" >> "$HOME/.bashrc"
    source "$HOME/.bashrc"
else
    echo "[ERROR] Executable not found. Build might have failed."
    exit 1
fi

# Run the tool
echo "[INFO] Running $TOOL_NAME..."
"$EXECUTABLE_PATH"

echo "[INFO] Installation and execution completed successfully."
