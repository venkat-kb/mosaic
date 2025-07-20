#!/usr/bin/env python3
"""
Multi-Language Grievance System Test Script
===========================================

This script demonstrates the enhanced grievance system with support for 15+ Indian languages.
It uses Gemini 2.5 Pro API for translation and processing.

Author: GitHub Copilot
Date: July 17, 2025
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from input import GeminiLanguageWrapper, extract_incident_details, INDIAN_LANGUAGES

def demo_language_support():
    """Demonstrate language detection and translation capabilities."""
    print("🌐 Multi-Language Grievance System Demo")
    print("=" * 50)
    
    wrapper = GeminiLanguageWrapper()
    
    # Sample grievances in different Indian languages
    sample_grievances = {
        "Hindi": "नमस्ते, मेरा नाम सुरेश है। मैं मुंबई से फोन कर रहा हूं। यहां बिजली की बहुत समस्या है।",
        "Bengali": "আমার নাম অনিতা। আমি কলকাতা থেকে ফোন করছি। এখানে পানির খুব সমস্যা।",
        "Telugu": "నా పేరు రవి. నేను హైదరాబాద్ నుండి కాల్ చేస్తున్నాను. ఇక్కడ రోడ్ చాలా చెడుగా ఉంది.",
        "Tamil": "என் பெயர் பிரியா. நான் சென்னையிலிருந்து அழைக்கிறேன். இங்கே குப்பை சேகரிப்பு இல்லை.",
        "Marathi": "माझे नाव अनिल आहे। मी पुण्याहून फोन करत आहे। इथे पाणी पुरवठा बंद आहे।",
        "Gujarati": "મારું નામ મીનાક્ષી છે. હું અમદાવાદથી ફોન કરું છું. અહીં શેરીઓ ખૂબ ગંદી છે.",
        "Kannada": "ನನ್ನ ಹೆಸರು ಅರುಣ್. ನಾನು ಬೆಂಗಳೂರಿನಿಂದ ಕರೆ ಮಾಡುತ್ತಿದ್ದೇನೆ. ಇಲ್ಲಿ ಟ್ರಾಫಿಕ್ ತುಂಬಾ ಕೆಟ್ಟದಾಗಿದೆ.",
        "Malayalam": "എന്റെ പേര് ശ്രീജ. ഞാൻ കൊച്ചിയിൽ നിന്ന് വിളിക്കുന്നു. ഇവിടെ മലിനജല പ്രശ്നമുണ്ട്.",
        "Punjabi": "ਮੇਰਾ ਨਾਮ ਹਰਪ੍ਰੀਤ ਹੈ। ਮੈਂ ਲੁਧਿਆਣੇ ਤੋਂ ਫੋਨ ਕਰ ਰਿਹਾ ਹਾਂ। ਇੱਥੇ ਬਿਜਲੀ ਦੀ ਬਹੁਤ ਸਮੱਸਿਆ ਹੈ।",
        "Odia": "ମୋର ନାମ ସୁନୀତା। ମୁଁ ଭୁବନେଶ୍ୱରରୁ ଫୋନ କରୁଛି। ଏଠାରେ ଦରିଦ୍ର ପରିଷ୍କାର ବ୍ୟବସ୍ଥା।"
    }
    
    print(f"📋 Testing {len(sample_grievances)} languages:")
    print(f"Supported languages: {', '.join(INDIAN_LANGUAGES.keys())}")
    print("-" * 50)
    
    for language, grievance in sample_grievances.items():
        print(f"\n🔸 {language} Test:")
        print(f"   Original: {grievance}")
        
        try:
            # Detect language
            detected = wrapper.detect_language(grievance)
            print(f"   Detected: {detected}")
            
            # Translate to English
            english_text = wrapper.translate_to_english(grievance, detected)
            print(f"   English: {english_text}")
            
            # Extract incident details
            details = extract_incident_details(english_text)
            print(f"   Status: ✅ Processed successfully")
            
        except Exception as e:
            print(f"   Status: ❌ Error - {e}")
    
    print("\n" + "=" * 50)
    print("✅ Demo completed!")

def show_usage():
    """Show usage instructions."""
    print("""
📖 How to Test the Multi-Language Grievance System
=================================================

1. **Setup Requirements:**
   ```
   pip install -r requirements.txt
   ```

2. **Configure API Key:**
   - Copy .env.template to .env
   - Add your Gemini API key to .env file

3. **Testing Options:**

   a) **Test Translation Only:**
      ```
      python input.py --test-translation
      ```

   b) **Test Grievance Processing:**
      ```
      python input.py --test-processing
      ```

   c) **Run All Tests:**
      ```
      python input.py --test-all
      ```

   d) **Run Full System (with speech):**
      ```
      python input.py
      ```

   e) **Run This Demo:**
      ```
      python test_demo.py
      ```

4. **Integration:**
   - Import the GrievanceAgent class in your main project
   - Use the enhanced input.py as a module
   - The Grievance object format remains the same

5. **Supported Languages:**
   Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Urdu, 
   Kannada, Odia, Punjabi, Malayalam, Assamese, Maithili, 
   Santali, Kashmiri + English

6. **Features:**
   ✅ Real-time language detection
   ✅ Automatic translation to English for processing
   ✅ Response translation back to user's language
   ✅ Same input/output format as original
   ✅ Gemini 2.5 Pro API integration
   ✅ Error handling and fallbacks
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_language_support()
    else:
        show_usage()
        print("\nRun with --demo to see language processing demonstration")
