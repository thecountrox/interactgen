#!/usr/bin/env python3
"""
Test script for Gemini API integration
Run this to verify your Gemini API key is working correctly
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🧪 Testing Gemini API Integration\n")
print("=" * 50)

# Check API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in environment variables")
    print("   Please add it to your .env file")
    exit(1)

print(f"✓ GEMINI_API_KEY found: {GEMINI_API_KEY[:10]}...")
print()

# Import Gemini
try:
    import google.generativeai as genai
    print("✓ google-generativeai package imported successfully")
except ImportError:
    print("❌ google-generativeai not installed")
    print("   Run: uv pip install google-generativeai")
    exit(1)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
print("✓ Gemini API configured")
print()

# Test 1: Generate Embedding
print("Test 1: Generating embedding...")
try:
    result = genai.embed_content(
        model="models/embedding-001",
        content="This is a test embedding for the browser automation agent.",
        task_type="retrieval_document"
    )
    embedding = result['embedding']
    print(f"✓ Embedding generated successfully")
    print(f"  - Dimension: {len(embedding)}")
    print(f"  - First 5 values: {embedding[:5]}")
    print()
except Exception as e:
    print(f"❌ Embedding generation failed: {e}")
    print()

# Test 2: Generate LLM Response
print("Test 2: Generating LLM response...")
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        "You are a helpful browser automation assistant. "
        "Say hello and introduce yourself in one sentence."
    )
    print(f"✓ LLM response generated successfully")
    print(f"  - Response: {response.text}")
    print()
except Exception as e:
    print(f"❌ LLM generation failed: {e}")
    print()

# Test 3: Test async functions from gemini_api module
print("Test 3: Testing gemini_api module...")
try:
    from gemini_api import generate_embedding, call_gemini_with_context
    print("✓ gemini_api module imported successfully")
    
    async def test_async():
        # Test async embedding
        emb = await generate_embedding("Test async embedding")
        print(f"  - Async embedding dimension: {len(emb)}")
        
        # Test judge function
        result = await call_gemini_with_context(
            page_context={
                "url": "https://example.com",
                "html_content": "<html><body>Example</body></html>",
                "metadata": {}
            },
            user_context={
                "technical_level": "intermediate",
                "personality_type": "analytical"
            },
            relevant_memories=None
        )
        print(f"  - Judge layer response: {len(result.get('suggestions', []))} suggestions")
        return result
    
    result = asyncio.run(test_async())
    print("✓ All async functions working")
    print()
    
except Exception as e:
    print(f"❌ gemini_api module test failed: {e}")
    print()

# Summary
print("=" * 50)
print("🎉 All tests completed!")
print()
print("Next steps:")
print("1. Start the FastAPI server: python main.py")
print("2. Visit http://localhost:8000/docs for API documentation")
print("3. Run the SQL script in Supabase SQL Editor")
print("4. Test the /analyze endpoint with your browser extension")
