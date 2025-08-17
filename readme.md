# Multi-Language Grievance System 🌐

An enhanced grievance processing system that supports **15+ Indian languages** with automatic translation using **Gemini 2.5 Pro API**.

## 🚀 Features

- **Multi-Language Support**: Hindi, Bengali, Telugu, Marathi, Tamil, Gujarati, Urdu, Kannada, Odia, Punjabi, Malayalam, Assamese, Maithili, Santali, Kashmiri + English
- **Real-time Translation**: Automatic language detection and translation using Gemini 2.5 Pro
- **Speech Recognition**: Enhanced speech recognition for Indian languages
- **Preserved Format**: Same input/output format as original system
- **Error Handling**: Robust error handling with fallbacks to English
- **Easy Integration**: Drop-in replacement for existing grievance system

## 🛠 Installation

1. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Setup API Key:**
   ```powershell
   # Copy template and add your Gemini API key
   copy .env.template .env
   # Edit .env file and add: GEMINI_API_KEY=your_actual_api_key
   ```

3. **Install PyAudio (for speech recognition):**
   ```powershell
   # For Windows, you might need to install manually
   pip install pipwin
   pipwin install pyaudio
   ```

## 🧪 Testing

### Quick Tests (No Speech Required)

1. **Test Translation Functionality:**
   ```powershell
   python input.py --test-translation
   ```

2. **Test Grievance Processing:**
   ```powershell
   python input.py --test-processing
   ```

3. **Run All Tests:**
   ```powershell
   python input.py --test-all
   ```

4. **Interactive Demo:**
   ```powershell
   python test_demo.py --demo
   ```

### Full System Test (With Speech)

```powershell
python input.py
```

## 📋 Usage Examples

### As a Module (Integration)

```python
from input import GrievanceAgent, GeminiLanguageWrapper

# Initialize the agent
agent = GrievanceAgent()

# Run the conversation (handles multi-language automatically)
grievance = agent.run_conversation()

# Process the result
if grievance:
    print(f"Caller: {grievance.caller_name}")
    print(f"Phone: {grievance.caller_phone_no}")
    print(f"Location: {grievance.location}")
    print(f"Description: {grievance.description}")
```

### Translation Only

```python
from input import GeminiLanguageWrapper

wrapper = GeminiLanguageWrapper()

# Detect language
text = "मुझे शिकायत करनी है"
language = wrapper.detect_language(text)
print(f"Detected: {language}")

# Translate to English
english_text = wrapper.translate_to_english(text, language)
print(f"English: {english_text}")
```

## 🔧 API Configuration

The system uses **Gemini 2.5 Pro** (`gemini-2.0-flash-exp`) for:
- Language detection
- Translation (bi-directional)
- Incident detail extraction
- Question generation

### Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

## 📊 Supported Languages

| Language | Code | Sample Phrase |
|----------|------|---------------|
| Hindi | hi | नमस्ते, मुझे शिकायत करनी है |
| Bengali | bn | আমার একটি অভিযোগ আছে |
| Telugu | te | నాకు ఒక ఫిర్యాదు ఉంది |
| Marathi | mr | मला तक्रार करायची आहे |
| Tamil | ta | எனக்கு ஒரு புகார் உள்ளது |
| Gujarati | gu | મને ફરિયાદ કરવી છે |
| Urdu | ur | مجھے شکایت کرنی ہے |
| Kannada | kn | ನನಗೆ ದೂರು ಇದೆ |
| Odia | or | ମୋର ଏକ ଅଭିଯୋଗ ଅଛି |
| Punjabi | pa | ਮੈਨੂੰ ਸ਼ਿਕਾਇਤ ਕਰਨੀ ਹੈ |
| Malayalam | ml | എനിക്ക് ഒരു പരാതിയുണ്ട് |
| Assamese | as | মোৰ এটা অভিযোগ আছে |
| Maithili | mai | हमरा शिकायत अछि |
| Santali | sat | ᱤᱧ ᱨᱮᱭᱟᱜ ᱚᱱᱚᱸᱛ ᱢᱮᱱᱟᱜ-ᱟ |
| Kashmiri | ks | میہ اک شکایت چھ |
| English | en | I have a complaint |

## 🏗 System Architecture

```
User Input (Any Language)
    ↓
Language Detection (Gemini)
    ↓
Translation to English (Gemini)
    ↓
Incident Processing (Gemini)
    ↓
Response Generation
    ↓
Translation to User Language (Gemini)
    ↓
Output (User's Language + English)
```

## 📱 Input/Output Format

### Input
- **Speech**: Multi-language speech input
- **Text**: Any supported language text

### Output (Preserved Format)
```python
Grievance {
    caller_name: str,
    caller_phone_no: str,
    description: str,
    location: str,
    date_time: str
}
```

## ⚡ Performance Notes

- **Language Detection**: ~1-2 seconds
- **Translation**: ~2-3 seconds
- **Processing**: ~3-5 seconds
- **Total**: ~6-10 seconds per interaction

## 🔒 Error Handling

- **Translation Failures**: Falls back to original text
- **API Errors**: Graceful degradation to English-only mode
- **Speech Recognition**: Multi-language fallback (Hindi → English)
- **Network Issues**: Offline error messages

## 🚀 Integration Guide

1. **Replace existing `input.py`** with the enhanced version
2. **Install new dependencies** from `requirements.txt`
3. **Add Gemini API key** to environment
4. **Test with sample data** before deployment
5. **No changes needed** in calling code - same interface

## 📞 Testing Phrases

Try these phrases in different languages:

**Hindi:** "नमस्ते, मेरा नाम राहुल है। मुझे दिल्ली में बिजली की समस्या की शिकायत करनी है।"

**Bengali:** "আমার নাম অমিত। কলকাতায় পানির সমস্যা নিয়ে অভিযোগ করতে চাই।"

**Tamil:** "என் பெயர் பிரியா. சென்னையில் குப்பை சேகரிப்பு பிரச்சனை உள்ளது."

## 🤝 Support

For issues or questions:
1. Check the test outputs with `--test-all`
2. Verify API key configuration
3. Test network connectivity
4. Review error logs in console

## 📄 License

Enhanced by GitHub Copilot for IBM Project
Original system preserved with multi-language capabilities added.
