import os
import requests
import json
import time
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
from models import Database
import uuid
import re
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import io
import traceback

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Configure APIs
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
CLIPDROP_API_KEY = os.getenv('CLIPDROP_API_KEY')

# Initialize database
db = Database()

# Ensure static directories exist
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/audio', exist_ok=True)

# Configure Gemini safety settings
generation_config = genai.types.GenerationConfig(
    temperature=0.7,
    top_k=32,
    top_p=0.8,
    max_output_tokens=1000,
)

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
]

class GeminiStoryGenerator:
    def __init__(self):
        try:
            self.model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            print("✅ Initialized Gemini 2.0 Flash model successfully")
        except Exception as e:
            print(f"❌ Error initializing Gemini model: {e}")
            raise

    def generate_pure_language_story(self, theme, language, age_group):
        """Generate story with title using Gemini API in selected language"""
        try:
            language_prompts = {
                "Hindi": f"""
                "{theme}" के बारे में हिंदी भाषा में एक बेहतरीन कहानी लिखें।
                निर्देश:
                - केवल हिंदी भाषा का उपयोग करें (अंग्रेजी शब्द बिल्कुल नहीं)
                - {age_group} आयु समूह के लिए उपयुक्त
                - 6 भागों में कहानी बनाएं
                - हर भाग में 60-70 शब्द
                
                JSON format में answer दें:
                {{
                  "title": "हिंदी में कहानी का शीर्षक",
                  "chunks": [
                    "पहला भाग...",
                    "दूसरा भाग...",
                    "तीसरा भाग...",
                    "चौथा भाग...",
                    "पांचवा भाग...",
                    "छठा भाग..."
                  ]
                }}
                महत्वपूर्ण: केवल JSON return करें, कोई extra text नहीं।
                """,
                
                "English": f"""
                Write an excellent story about "{theme}" in English language only.
                Instructions:
                - Use English language ONLY
                - Suitable for {age_group} age group
                - Create story in 6 parts
                - Each part should be 60-70 words
                
                Return in JSON format:
                {{
                  "title": "Story title in English",
                  "chunks": [
                    "First part...",
                    "Second part...",
                    "Third part...",
                    "Fourth part...",
                    "Fifth part...",
                    "Sixth part..."
                  ]
                }}
                IMPORTANT: Return only JSON, no extra text.
                """,
                
                "Marathi": f"""
                "{theme}" बद्दल मराठी भाषेत उत्कृष्ट कथा लिहा।
                सूचना:
                - फक्त मराठी भाषा वापरा (इंग्रजी शब्द बिल्कुल नको)
                - {age_group} वयोगटासाठी योग्य
                - 6 भागांत कथा तयार करा
                - प्रत्येक भागात 60-70 शब्द
                
                JSON format मध्ये उत्तर द्या:
                {{
                  "title": "मराठीत कथेचे शीर्षक",
                  "chunks": [
                    "पहिला भाग...",
                    "दुसरा भाग...",
                    "तिसरा भाग...",
                    "चौठा भाग...",
                    "पाचवा भाग...",
                    "सहावा भाग..."
                  ]
                }}
                महत्वाचे: फक्त JSON return करा, extra text नको.
                """,
                
                "Bengali": f"""
                "{theme}" সম্পর্কে বাংলা ভাষায় একটি চমৎকার গল্প লিখুন।
                নির্দেশনা:
                - শুধুমাত্র বাংলা ভাষা ব্যবহার করুন (কোন ইংরেজি শব্দ নয়)
                - {age_group} বয়সের গ্রুপের জন্য উপযুক্ত
                - ৬টি অংশে গল্প তৈরি করুন
                - প্রতিটি অংশে ৬০-৭০ শব্দ
                
                JSON ফরম্যাটে উত্তর দিন:
                {{
                  "title": "বাংলায় গল্পের শিরোনাম",
                  "chunks": [
                    "প্রথম অংশ...",
                    "দ্বিতীয় অংশ...",
                    "তৃতীয় অংশ...",
                    "চতুর্থ অংশ...",
                    "পঞ্চম অংশ...",
                    "ষষ্ঠ অংশ..."
                  ]
                }}
                """,
                
                "Tamil": f"""
                "{theme}" பற்றி தமிழ் மொழியில் ஒரு சிறந்த கதை எழுதுங்கள்।
                வழிமுறைகள்:
                - தமிழ் மொழியை மட்டுமே பயன்படுத்துங்கள் (ஆங்கில வார்த்தைகள் வேண்டாம்)
                - {age_group} வயதுக்குரிய குழுவிற்கு ஏற்றது
                - 6 பகுதிகளில் கதையை உருவாக்குங்கள்
                - ஒவ்வொரு பகுதியும் 60-70 வார்த்தைகள்
                
                JSON வடிவத்தில் பதில் கொடுங்கள்:
                {{
                  "title": "தமிழில் கதையின் தலைப்பு",
                  "chunks": [
                    "முதல் பகுতி...",
                    "இரண்டாவது பகுति...",
                    "மூன்றாவது பகுति...",
                    "நான்காவது பகுति...",
                    "ஐந்தாவது பகுति...",
                    "ஆறாவது பகுति..."
                  ]
                }}
                """,
                
                "Telugu": f"""
                "{theme}" గురించి తెలుగు భాషలో ఒక అద్భుతమైన కథ రాయండి।
                సూచనలు:
                - తెలుగు భాషను మాత్రమే ఉపయోగించండి (ఆంగ్ల పదాలు వద్దు)
                - {age_group} వయస్సు గ్రూపుకు తగినది
                - 6 భాగాల్లో కథను సృష్టించండి
                - ప్రతి భాగంలో 60-70 పదాలు
                
                JSON ఫార్మాట్‌లో సమాధానం ఇవ్వండి:
                {{
                  "title": "తెలుగులో కథ యొక్క శీర్షిక",
                  "chunks": [
                    "మొదటి భాగం...",
                    "రెండవ భాగం...",
                    "మూడవ భాగం...",
                    "నాలుగవ భాగం...",
                    "ఐదవ భాగం...",
                    "ఆరవ భాగం..."
                  ]
                }}
                """
            }
            
            prompt = language_prompts.get(language, language_prompts["English"])
            print(f"📝 Generating {language} story using Gemini...")
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                story_data = json.loads(json_text)
                title = story_data.get('title', f'{theme} Story')
                chunks = story_data.get('chunks', [])
                
                # Ensure we have 6 chunks
                while len(chunks) < 6:
                    chunks.append(self.create_additional_chunk(theme, language, len(chunks) + 1))
                
                return title, chunks[:6]
            else:
                raise Exception("Invalid JSON response from Gemini")
                
        except Exception as e:
            print(f"❌ Gemini story generation failed: {e}")
            return self.get_fallback_story(theme, language)

    def create_additional_chunk(self, theme, language, chapter_num):
        additional_chunks = {
            "Hindi": f"अध्याय {chapter_num} में {theme} की कहानी और भी रोचक हो जाती है।",
            "English": f"Chapter {chapter_num} makes the story of {theme} even more fascinating.",
            "Marathi": f"अध्याय {chapter_num} मध्ये {theme} ची कथा अधिकच मनोरंजक होते।",
            "Bengali": f"অধ্যায় {chapter_num}-এ {theme}-এর গল্প আরও আকর্ষণীয় হয়ে ওঠে।",
            "Tamil": f"அத্தியாயம் {chapter_num}-ல் {theme} கதை இன்னும் சुवारসியमানतাக মাড়ুকিறিতু।",
            "Telugu": f"అధ్యాయం {chapter_num}లో {theme} కథ మరింత ఆసక్తికరంగా మారుతుంది।"
        }
        return additional_chunks.get(language, additional_chunks["English"])

    def get_fallback_story(self, theme, language):
        fallback_stories = {
            "Hindi": {
                "title": f"{theme} की अद्भुत यात्रा",
                "chunks": [
                    f"{theme} की यह जादुई कहानी एक अनोखी दुनिया से शुरू होती है।",
                    "यात्रा के दौरान मुख्य पात्र कई अनूठे लोगों से मिलता है।",
                    "कहानी में कई रहस्यमय तत्व धीरे-धीरे सामने आते हैं।",
                    "चुनौतियां कठिन होती जाती हैं लेकिन साहस बढ़ता जाता है।",
                    "अंतिम चुनौती सबसे कठिन साबित होती है।",
                    "कहानी खुशी के साथ समाप्त होती है और सभी सीख प्राप्त करते हैं।"
                ]
            },
            "English": {
                "title": f"The Amazing Adventure of {theme}",
                "chunks": [
                    f"The magical story of {theme} begins in an extraordinary world.",
                    "During this journey, the main character meets unique companions.",
                    "The story contains mysterious elements that gradually unfold.",
                    "Challenges become difficult but courage continues growing.",
                    "The final challenge proves most difficult to overcome.",
                    "The story concludes with joy as characters learn valuable lessons."
                ]
            }
        }
        
        story = fallback_stories.get(language, fallback_stories["English"])
        return story["title"], story["chunks"]

class ClipdropImageGenerator:
    def __init__(self):
        self.api_key = CLIPDROP_API_KEY
        if not self.api_key:
            raise ValueError("CLIPDROP_API_KEY environment variable is not set")
        self.api_url = 'https://clipdrop-api.co/text-to-image/v1'
        
        try:
            self.prompt_model = genai.GenerativeModel(
                model_name='gemini-2.0-flash',
                generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=1000)
            )
            print("✅ Initialized Gemini for English prompts")
        except Exception as e:
            print(f"⚠️ Could not initialize Gemini: {e}")
            self.prompt_model = None

    def generate_image(self, chunk_text, image_style, index, story_theme=None):
        try:
            print(f"🎨 Generating Clipdrop image {index+1}/6...")
            
            headers = {'x-api-key': self.api_key}
            prompt = self.create_english_visual_prompt(chunk_text, image_style, story_theme)
            files = {'prompt': (None, prompt, 'text/plain')}
            
            response = requests.post(self.api_url, headers=headers, files=files)
            
            if response.status_code == 200:
                filename = f"clipdrop_{uuid.uuid4().hex}_{index}.png"
                filepath = f"static/images/{filename}"
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Clipdrop image {index+1} generated successfully")
                return filepath
            else:
                print(f"❌ Clipdrop error: {response.text}")
                return self.create_placeholder(index, f"Image generation failed")
                
        except Exception as e:
            print(f"❌ Clipdrop image generation failed: {e}")
            return self.create_placeholder(index, str(e))

    def create_english_visual_prompt(self, chunk_text, image_style, story_theme=None):
        """Create English prompt for image generation"""
        style_base = {
            "cartoon": "Disney Pixar style, vibrant colors, cute and expressive characters",
            "comic": "comic book style, dynamic action, bold colors, strong outlines", 
            "anime": "anime style, expressive faces, beautiful backgrounds",
            "realistic": "photorealistic, detailed textures, natural lighting",
            "watercolor": "soft watercolor style, gentle colors, artistic feel",
            "oil_painting": "oil painting style, rich colors, classical look"
        }
        
        style_prompt = style_base.get(image_style, style_base["cartoon"])
        
        if self.prompt_model:
            try:
                prompt = f"""Convert this story text to an English visual description: "{chunk_text}"
                Create a detailed English image prompt that captures the main scene and characters.
                Reply only in English. Keep under 150 characters."""
                
                response = self.prompt_model.generate_content(prompt)
                if hasattr(response, 'text'):
                    visual_prompt = response.text.strip().replace('\n', ' ')
                    final_prompt = f"{visual_prompt}. {style_prompt}. High quality illustration."
                    return final_prompt[:300]
                    
            except Exception as e:
                print(f"⚠️ Error generating English prompt: {e}")
        
        scene_description = f"A {image_style} style scene showing beautiful cultural story elements"
        return f"{scene_description}. {style_prompt}. High quality illustration."

    def create_placeholder(self, index, description):
        try:
            filename = f"placeholder_{index}_{uuid.uuid4().hex}.jpg"
            filepath = f"static/images/{filename}"
            
            img = Image.new('RGB', (1024, 1024), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
            
            title = f"Chapter {index+1}"
            bbox = draw.textbbox((0, 0), title, font=font)
            width = bbox[2] - bbox[0]
            x = (1024 - width) // 2
            draw.text((x, 400), title, fill='#000000', font=font)
            
            img.save(filepath, quality=95, optimize=True)
            return filepath
            
        except Exception as e:
            print(f"❌ Error creating placeholder: {e}")
            return None

# Professional Audio Generator using ElevenLabs API
class ProfessionalAudioGenerator:
    def __init__(self):
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        # Voice IDs for different languages (you'll need to get these from ElevenLabs)
        self.voice_mapping = {
            'Hindi': 'pNInz6obpgDQGcFmaJgB',  # Sample voice ID
            'English': '21m00Tcm4TlvDq8ikWAM', # Sample voice ID  
            'Marathi': 'pNInz6obpgDQGcFmaJgB',
            'Bengali': 'pNInz6obpgDQGcFmaJgB',
            'Tamil': 'pNInz6obpgDQGcFmaJgB',
            'Telugu': 'pNInz6obpgDQGcFmaJgB'
        }
        
        if self.elevenlabs_api_key:
            print("✅ Professional Audio Generator (ElevenLabs) initialized")
        else:
            print("⚠️ ElevenLabs API key not found - using fallback")

    def generate_audio(self, text, language):
        """Generate high-quality audio using ElevenLabs API"""
        
        if not self.elevenlabs_api_key:
            return self.create_simple_audio_placeholder(text, language)
        
        try:
            voice_id = self.voice_mapping.get(language, self.voice_mapping['English'])
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.5,
                    "use_speaker_boost": True
                }
            }
            
            print(f"🎤 Generating professional audio for {language}...")
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                filename = f"professional_audio_{uuid.uuid4().hex}.mp3"
                filepath = f"static/audio/{filename}"
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Professional audio generated successfully for {language}")
                return filepath
            else:
                print(f"❌ ElevenLabs API error: {response.text}")
                return self.create_simple_audio_placeholder(text, language)
                
        except Exception as e:
            print(f"❌ Professional audio generation failed: {e}")
            return self.create_simple_audio_placeholder(text, language)

    def create_simple_audio_placeholder(self, text, language):
        """Create a simple audio data file as placeholder"""
        try:
            audio_data = {
                "type": "tts_placeholder",
                "text": text,
                "language": language,
                "voice_settings": {
                    "rate": 0.8,
                    "pitch": 1.0,
                    "volume": 1.0
                },
                "duration_estimate": len(text.split()) * 0.5  # Rough estimate
            }
            
            filename = f"audio_placeholder_{uuid.uuid4().hex}.json"
            filepath = f"static/audio/{filename}"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(audio_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Audio placeholder created for {language}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error creating audio placeholder: {e}")
            return None

# Helper function to get chapter text in selected language
def get_chapter_text(language, chapter_num):
    """Get 'Chapter' text in selected language"""
    chapter_texts = {
        "Hindi": "अध्याय",
        "English": "Chapter", 
        "Marathi": "प्रकरण",
        "Bengali": "অধ্যায়",
        "Tamil": "அத্তியாயம்",
        "Telugu": "అధ্যাయం"
    }
    return f"{chapter_texts.get(language, 'Chapter')} {chapter_num}"

# Initialize generators
story_gen = GeminiStoryGenerator()
image_gen = ClipdropImageGenerator()
audio_gen = ProfessionalAudioGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    theme = request.form.get('theme')
    language = request.form.get('language')
    age_group = request.form.get('age_group')
    image_style = request.form.get('image_style', 'cartoon')
    
    if not theme or not language or not age_group:
        flash('Please fill all fields.', 'error')
        return redirect(url_for('index'))
    
    try:
        print(f"🚀 Starting generation for '{theme}' in {language}")
        
        # Generate story in selected language
        story_title, chunks = story_gen.generate_pure_language_story(theme, language, age_group)
        print(f"✅ Story generated in {language}: '{story_title}'")
        print(f"📝 Generated {len(chunks)} story chunks")
        
        # Generate images with English prompts
        print("🎨 Generating images...")
        image_results = []
        
        for i, chunk in enumerate(chunks):
            try:
                image_path = image_gen.generate_image(chunk, image_style, i, theme)
                image_results.append(image_path)
            except Exception as e:
                print(f"Image {i+1} failed: {e}")
                placeholder = image_gen.create_placeholder(i, f"Scene {i+1}")
                image_results.append(placeholder)
        
        # Generate professional audio
        print(f"🎤 Generating professional audio for {language}...")
        audio_path = None
        if audio_gen:
            try:
                full_story = " ".join(chunks)
                audio_path = audio_gen.generate_audio(full_story, language)
            except Exception as e:
                print(f"Audio generation failed: {e}")
        
        print("🎉 Generation completed!")
        
        return render_template('generate_new.html',
                               story_title=story_title,
                               theme=theme,
                               language=language,
                               age_group=age_group,
                               image_style=image_style,
                               chunks=chunks,
                               image_paths=image_results,
                               audio_path=audio_path,
                               get_chapter_text=get_chapter_text)
                               
    except Exception as e:
        print(f"❌ Generation error: {e}")
        traceback.print_exc()
        flash(f'Error generating story: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/save_story', methods=['POST'])
def save_story():
    """COMPLETELY FIXED save function with detailed debugging"""
    
    # DETAILED DEBUGGING
    print("="*80)
    print("🔍 SAVE STORY DEBUGGING:")
    print(f"Request method: {request.method}")
    print(f"Content type: {request.content_type}")
    print(f"Form keys: {list(request.form.keys())}")
    
    for key, value in request.form.items():
        if len(str(value)) > 100:
            print(f"  {key}: {str(value)[:100]}... (length: {len(str(value))})")
        else:
            print(f"  {key}: {value}")
    print("="*80)
    
    try:
        # Get basic form data
        story_title = request.form.get('story_title', '').strip()
        theme = request.form.get('theme', '').strip()
        language = request.form.get('language', '').strip()
        age_group = request.form.get('age_group', '').strip()
        
        # Get JSON strings
        chunks_raw = request.form.get('chunks', '')
        image_paths_raw = request.form.get('image_paths', '')
        
        print(f"📝 EXTRACTED DATA:")
        print(f"  Title: '{story_title}'")
        print(f"  Theme: '{theme}'")
        print(f"  Language: '{language}'")
        print(f"  Age group: '{age_group}'")
        print(f"  Chunks raw type: {type(chunks_raw)}")
        print(f"  Chunks raw length: {len(chunks_raw)}")
        print(f"  Chunks preview: '{chunks_raw[:200]}...'")
        print(f"  Image paths raw type: {type(image_paths_raw)}")
        print(f"  Image paths raw length: {len(image_paths_raw)}")
        
        # Initialize
        chunks = []
        image_paths = []
        
        # ULTRA SAFE chunks parsing
        if chunks_raw:
            print(f"🔍 PROCESSING CHUNKS:")
            
            # Clean the raw string
            chunks_clean = chunks_raw.strip()
            
            if chunks_clean and chunks_clean not in ['', 'undefined', 'null', 'None', '[]']:
                print(f"  Clean chunks string: '{chunks_clean[:100]}...'")
                
                try:
                    # Parse JSON
                    chunks_parsed = json.loads(chunks_clean)
                    print(f"  JSON parsed successfully: {type(chunks_parsed)}")
                    
                    if isinstance(chunks_parsed, list):
                        chunks = [str(chunk) for chunk in chunks_parsed if chunk]
                        print(f"  ✅ Got {len(chunks)} valid chunks")
                    elif isinstance(chunks_parsed, str):
                        chunks = [chunks_parsed]
                        print(f"  ✅ Converted single string to list")
                    else:
                        print(f"  ❌ Unexpected type: {type(chunks_parsed)}")
                        chunks = []
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON decode error: {e}")
                    print(f"  ❌ Raw string causing error: '{chunks_clean}'")
                    chunks = []
                except Exception as e:
                    print(f"  ❌ Other parsing error: {e}")
                    chunks = []
            else:
                print(f"  ⚠️ Empty or invalid chunks string")
        else:
            print(f"  ⚠️ No chunks raw data received")
        
        # ULTRA SAFE image paths parsing
        if image_paths_raw:
            print(f"🔍 PROCESSING IMAGE PATHS:")
            
            image_paths_clean = image_paths_raw.strip()
            
            if image_paths_clean and image_paths_clean not in ['', 'undefined', 'null', 'None', '[]']:
                try:
                    image_paths_parsed = json.loads(image_paths_clean)
                    
                    if isinstance(image_paths_parsed, list):
                        image_paths = [str(path) for path in image_paths_parsed if path]
                        print(f"  ✅ Got {len(image_paths)} image paths")
                    elif isinstance(image_paths_parsed, str):
                        image_paths = [image_paths_parsed]
                        print(f"  ✅ Converted single path to list")
                    else:
                        image_paths = []
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ Image paths JSON error: {e}")
                    image_paths = []
                except Exception as e:
                    print(f"  ❌ Image paths other error: {e}")
                    image_paths = []
        
        # Get other fields
        audio_path = request.form.get('audio_path', '').strip()
        image_style = request.form.get('image_style', 'cartoon').strip()
        
        print(f"📊 FINAL PROCESSED DATA:")
        print(f"  Chunks: {len(chunks)} items - {chunks[:2] if chunks else 'EMPTY'}")
        print(f"  Image paths: {len(image_paths)} items")
        print(f"  Audio path: '{audio_path}'")
        print(f"  Image style: '{image_style}'")
        
        # DETAILED VALIDATION
        validation_errors = []
        
        if not story_title:
            validation_errors.append("Story title missing")
        if not theme:
            validation_errors.append("Theme missing") 
        if not language:
            validation_errors.append("Language missing")
        if not chunks:
            validation_errors.append("Story chunks missing or empty")
            
        if validation_errors:
            error_msg = f"Validation failed: {', '.join(validation_errors)}"
            print(f"❌ {error_msg}")
            flash(error_msg, 'error')
            return redirect(url_for('index'))
        
        # SAVE TO DATABASE
        print(f"💾 SAVING TO DATABASE:")
        print(f"  Theme: {theme}")
        print(f"  Language: {language}")
        print(f"  Age group: {age_group}")
        print(f"  Chunks count: {len(chunks)}")
        print(f"  Image paths count: {len(image_paths)}")
        print(f"  Audio path: {audio_path}")
        print(f"  Image style: {image_style}")
        
        story_id = db.save_story(
            theme=theme,
            language=language,
            age_group=age_group,
            chunks=chunks,
            image_paths=image_paths,
            audio_path=audio_path,
            image_style=image_style
        )
        
        print(f"✅ SUCCESS: Story saved with ID {story_id}")
        flash('Story saved successfully! 🎉', 'success')
        return redirect(url_for('view_story', story_id=story_id))
        
    except Exception as e:
        print(f"❌ FATAL ERROR in save_story: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Error saving story: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/stories')
def stories():
    try:
        all_stories = db.get_all_stories()
        for story in all_stories:
            if not isinstance(story.get('chunks', []), list):
                story['chunks'] = []
        return render_template('stories.html', stories=all_stories)
    except Exception as e:
        print(f"❌ Error retrieving stories: {e}")
        flash('Error loading stories', 'error')
        return redirect(url_for('index'))

@app.route('/story/<int:story_id>')
def view_story(story_id):
    story = db.get_story(story_id)
    if not story:
        flash('Story not found.', 'error')
        return redirect(url_for('stories'))
    return render_template('story.html', story=story, get_chapter_text=get_chapter_text)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
