#!/usr/bin/env python
"""
Test script to verify JSON parsing from ChatGPT responses
"""
import json
import re

def test_json_parsing():
    """Test JSON parsing with various ChatGPT response formats"""
    
    # Test case 1: JSON wrapped in markdown code blocks
    test_response_1 = """```json
{
    "type": "top",
    "color": "blue",
    "style": "formal",
    "material": "cotton",
    "pattern": "solid",
    "occasion": "business",
    "season": "all"
}
```"""
    
    # Test case 2: JSON without code blocks
    test_response_2 = """{
    "type": "bottom",
    "color": "black",
    "style": "casual",
    "material": "denim",
    "pattern": "solid",
    "occasion": "casual",
    "season": "all"
}"""
    
    # Test case 3: JSON with extra text
    test_response_3 = """Here's the analysis:
{
    "type": "shoes",
    "color": "brown",
    "style": "formal",
    "material": "leather",
    "pattern": "solid",
    "occasion": "formal",
    "season": "all"
}
That's the complete analysis."""
    
    def parse_chatgpt_response(response_text):
        """Parse ChatGPT response to extract JSON"""
        try:
            # First, try direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            try:
                # Look for JSON in markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    return json.loads(json_str)
                
                # Try to find JSON object without code blocks
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)
            except (json.JSONDecodeError, AttributeError):
                pass
            
            # Return None if parsing fails
            return None
    
    print("🧪 Testing JSON Parsing from ChatGPT Responses")
    print("=" * 50)
    
    # Test all cases
    test_cases = [
        ("Markdown code blocks", test_response_1),
        ("Plain JSON", test_response_2),
        ("JSON with extra text", test_response_3)
    ]
    
    for test_name, test_response in test_cases:
        print(f"\n📝 Test: {test_name}")
        print(f"Response: {test_response[:100]}...")
        
        result = parse_chatgpt_response(test_response)
        
        if result:
            print("✅ Successfully parsed JSON:")
            print(f"   Type: {result.get('type', 'N/A')}")
            print(f"   Color: {result.get('color', 'N/A')}")
            print(f"   Style: {result.get('style', 'N/A')}")
            print(f"   Material: {result.get('material', 'N/A')}")
            print(f"   Pattern: {result.get('pattern', 'N/A')}")
            print(f"   Occasion: {result.get('occasion', 'N/A')}")
            print(f"   Season: {result.get('season', 'N/A')}")
        else:
            print("❌ Failed to parse JSON")
    
    print("\n🎉 JSON parsing tests completed!")

if __name__ == "__main__":
    test_json_parsing()
