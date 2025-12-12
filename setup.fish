#!/usr/bin/env fish
echo "Setting up the Backend..."
if not command -v uv &> /dev/null
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "uv installed. Please restart your shell or run: source ~/.cargo/env"
    exit 0
end

echo "✓ uv found: "(uv --version)

if not command -v python3 &> /dev/null
    echo "Python 3 is not installed. Please install Python 3.8+"
    exit 1
end

echo "Python found: "(python3 --version)

echo ""
echo "Creating virtual environment with uv..."
uv venv

echo ""
echo "Activating virtual environment..."
source .venv/bin/activate.fish

echo ""
echo "Installing dependencies with uv..."
uv pip install -r requirements.txt

echo ""
echo "Installing Playwright browsers..."
playwright install chromium

if not test -f .env
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env and add your credentials!"
else
    echo ""
    echo ".env file already exists"
end

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Supabase and OpenAI credentials"
echo "2. Run the SQL script (supabase_setup.sql) in Supabase SQL Editor"
echo "3. Activate the virtual environment: source venv/bin/activate.fish"
echo "4. Start the server: python main.py"
echo ""
echo "Documentation: http://localhost:8000/docs (after starting server)"
