import os
import webbrowser
import warnings
import io
import base64
import subprocess

from flask import Flask, render_template, request, jsonify

from deepface import DeepFace

import numpy as np
import cv2
import yt_dlp
import soundfile as sf
import librosa
import torch

from transformers import pipeline
app = Flask(__name__)
# ============================================================
# VOICE EMOTION MODEL
# ============================================================

voice_emotion_model = None


def get_voice_emotion_model():
    """Load the speech-emotion model only when voice detection is used."""
    global voice_emotion_model

    if voice_emotion_model is None:
        print("🎤 Loading voice emotion model...")
        voice_emotion_model = pipeline(
            "audio-classification",
            model="superb/wav2vec2-base-superb-er"
        )
        print("✅ Voice emotion model loaded")

    return voice_emotion_model

# ============================================================
# YOUTUBE URL CACHE
# ============================================================

youtube_cache = {}


# ============================================================
# GET DIRECT YOUTUBE URL
# ============================================================

# ============================================================
# SMART YOUTUBE URL FINDER
# ============================================================

youtube_cache = {}


def normalize_text(text):
    """Make text easier to compare."""
    if not text:
        return ""

    return (
        str(text)
        .lower()
        .replace("&", "and")
        .replace("-", " ")
        .replace("_", " ")
        .replace("!", "")
        .replace("?", "")
        .replace("'", "")
        .replace('"', "")
    )


def get_youtube_url(song_title, artist, language="english"):

    cache_key = (
        f"{song_title}|{artist}|{language}"
        .lower()
        .strip()
    )

    # Use cached result if available
    if cache_key in youtube_cache:

        print(f"🎵 Using cached URL: {song_title}")

        return youtube_cache[cache_key]

    try:

        print(
            f"🔎 Searching YouTube: "
            f"{song_title} - {artist} - {language}"
        )

        # Search multiple results instead of blindly
        # taking the first YouTube result.
        search_query = (
            f"ytsearch8:"
            f"{song_title} "
            f"{artist} "
            f"{language} "
            f"official"
        )

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            result = ydl.extract_info(
                search_query,
                download=False
            )

        entries = []

        if result:
            entries = result.get("entries") or []

        if not entries:

            print(
                f"❌ No YouTube results found: "
                f"{song_title}"
            )

            return None

        target_title = normalize_text(song_title)
        target_artist = normalize_text(artist)

        best_video = None
        best_score = -1

        # Compare every search result
        for video in entries:

            if not video:
                continue

            video_title = normalize_text(
                video.get("title", "")
            )

            channel = normalize_text(
                video.get("channel", "")
            )

            uploader = normalize_text(
                video.get("uploader", "")
            )

            score = 0

            # ----------------------------------------
            # EXACT SONG TITLE MATCH
            # ----------------------------------------

            if target_title and target_title in video_title:
                score += 100

            # ----------------------------------------
            # WORD MATCHING
            # ----------------------------------------

            title_words = set(
                target_title.split()
            )

            result_words = set(
                video_title.split()
            )

            if title_words:

                matching_words = (
                    title_words & result_words
                )

                score += (
                    len(matching_words)
                    / len(title_words)
                ) * 50

            # ----------------------------------------
            # ARTIST / MOVIE MATCH
            # ----------------------------------------

            artist_words = set(
                target_artist.split()
            )

            channel_words = set(
                channel.split()
            )

            uploader_words = set(
                uploader.split()
            )

            if artist_words:

                artist_matches = (
                    artist_words & channel_words
                )

                artist_matches |= (
                    artist_words & uploader_words
                )

                score += len(artist_matches) * 15

            # ----------------------------------------
            # OFFICIAL VIDEO BONUS
            # ----------------------------------------

            if "official" in video_title:
                score += 10

            # ----------------------------------------
            # VIDEO ID
            # ----------------------------------------

            video_id = video.get("id")

            if not video_id:
                continue

            print(
                f"   🎵 Candidate: "
                f"{video.get('title', '')} "
                f"| Score: {score:.1f}"
            )

            if score > best_score:

                best_score = score
                best_video = video

        # ----------------------------------------
        # ACCEPT ONLY A GOOD MATCH
        # ----------------------------------------

        if best_video and best_score >= 60:

            video_id = best_video.get("id")

            youtube_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )

            youtube_cache[cache_key] = youtube_url

            print(
                f"✅ Correct song found: "
                f"{best_video.get('title', '')}"
            )

            print(
                f"🔗 YouTube URL: {youtube_url}"
            )

            return youtube_url

        print(
            f"⚠️ No reliable match found for: "
            f"{song_title}"
        )

        return None

    except Exception as e:

        print(
            f"❌ YouTube search error for "
            f"{song_title}: {e}"
        )

        return None

# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# EMOTION ANALYSIS
# ============================================================

@app.route("/analyze-emotion", methods=["POST"])
def analyze_emotion():

    try:

        print("\n📷 Image received")
        print("🤖 Starting emotion analysis...")

        frame = None

        # ----------------------------------------------------
        # OPTION 1: JSON IMAGE
        # ----------------------------------------------------

        if request.is_json:

            data = request.get_json(silent=True)

            if not data:

                return jsonify({
                    "success": False,
                    "error": "Empty JSON request"
                }), 400

            image_data = data.get("image")

            if not image_data:

                return jsonify({
                    "success": False,
                    "error": "Image not found in JSON"
                }), 400

            # Remove base64 header
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]

            # Decode base64
            image_bytes = base64.b64decode(image_data)

            # Convert to NumPy
            np_array = np.frombuffer(
                image_bytes,
                np.uint8
            )

            # Convert to OpenCV image
            frame = cv2.imdecode(
                np_array,
                cv2.IMREAD_COLOR
            )


        # ----------------------------------------------------
        # OPTION 2: FORMDATA IMAGE
        # ----------------------------------------------------

        else:

            image_file = None

            if "image" in request.files:

                image_file = request.files["image"]

            elif "file" in request.files:

                image_file = request.files["file"]

            elif "photo" in request.files:

                image_file = request.files["photo"]


            if image_file is None:

                return jsonify({
                    "success": False,
                    "error": "No image file received"
                }), 400


            # Read uploaded image
            image_bytes = image_file.read()


            # Convert to NumPy
            np_array = np.frombuffer(
                image_bytes,
                np.uint8
            )


            # Convert to OpenCV
            frame = cv2.imdecode(
                np_array,
                cv2.IMREAD_COLOR
            )


        # ----------------------------------------------------
        # CHECK IMAGE
        # ----------------------------------------------------

        if frame is None:

            return jsonify({
                "success": False,
                "error": "Could not decode image"
            }), 400


        print("🖼️ Image decoded successfully")
        print("🤖 Running DeepFace...")


        # ----------------------------------------------------
        # DEEPFACE EMOTION ANALYSIS
        # ----------------------------------------------------

        result = DeepFace.analyze(

            img_path=frame,

            actions=["emotion"],

            detector_backend="retinaface",

            enforce_detection=False
        )


        # ----------------------------------------------------
        # DEEPFACE MAY RETURN A LIST
        # ----------------------------------------------------

        if isinstance(result, list):

            if len(result) == 0:

                return jsonify({
                    "success": False,
                    "error": "No face analysis result"
                }), 500

            result = result[0]


        # ----------------------------------------------------
        # GET EMOTION DATA
        # ----------------------------------------------------

        emotions = result.get(
            "emotion",
            {}
        )


        if not emotions:

            return jsonify({
                "success": False,
                "error": "Emotion data not found"
            }), 500


        # ----------------------------------------------------
        # FIND HIGHEST EMOTION
        # ----------------------------------------------------

        detected_emotion = max(

            emotions,

            key=lambda emotion:
                float(emotions[emotion])

        )


        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence = float(
            emotions[detected_emotion]
        )


        print(
            f"😊 Detected emotion: {detected_emotion}"
        )


        print(
            f"📊 Confidence: {confidence:.2f}%"
        )


        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "emotion":
                str(detected_emotion),

            "confidence":
                confidence

        })


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print(
            "❌ Emotion analysis error:",
            str(e)
        )


        return jsonify({

            "success": False,

            "error":
                str(e)

        }), 500



# ============================================================
# VOICE EMOTION ANALYSIS
# ============================================================

@app.route("/analyze-voice", methods=["POST"])
def analyze_voice():

    try:
        print("\n🎤 Voice received")
        print("🤖 Starting voice emotion analysis...")

        if "audio" not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio file received"
            }), 400

        audio_file = request.files["audio"]
        audio_bytes = audio_file.read()

        if not audio_bytes:
            return jsonify({
                "success": False,
                "error": "Audio file is empty"
            }), 400

        # Read WAV data sent by the browser.
        audio_data, sample_rate = sf.read(
            io.BytesIO(audio_bytes),
            dtype="float32"
        )

        # Stereo -> mono.
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)

        # The SUPERB model expects 16 kHz audio.
        if int(sample_rate) != 16000:
            audio_data = librosa.resample(
                audio_data,
                orig_sr=int(sample_rate),
                target_sr=16000
            )
            sample_rate = 16000

        # Normalize safely.
        audio_data = np.asarray(audio_data, dtype=np.float32)

        max_value = np.max(np.abs(audio_data))
        if max_value > 0:
            audio_data = audio_data / max_value

        model = get_voice_emotion_model()

        results = model({
            "raw": audio_data,
            "sampling_rate": int(sample_rate)
        })

        print("🎤 Voice model results:", results)

        if not results:
            return jsonify({
                "success": False,
                "error": "Could not detect voice emotion."
            }), 500

        top_result = results[0]

        label = str(top_result.get("label", "")).lower().strip()
        score = float(top_result.get("score", 0.0))

        # SUPERB emotion labels:
        # hap = happy, sad = sad, ang = angry, neu = neutral
        emotion_map = {
            "hap": "happy",
            "happy": "happy",
            "sad": "sad",
            "ang": "angry",
            "angry": "angry",
            "neu": "neutral",
            "neutral": "neutral"
        }

        detected_emotion = emotion_map.get(label, "neutral")
        confidence = score * 100.0

        print(
            f"🎤 Detected voice emotion: "
            f"{detected_emotion}"
        )
        print(
            f"📊 Voice confidence: "
            f"{confidence:.2f}%"
        )

        return jsonify({
            "success": True,
            "emotion": detected_emotion,
            "confidence": confidence
        })

    except Exception as e:
        print("❌ Voice emotion error:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# OPEN YOUTUBE IN GOOGLE CHROME
# ============================================================

@app.route("/open-youtube")
def open_youtube():

    url = request.args.get("url", "").strip()

    # Only allow normal YouTube watch URLs
    if not url.startswith("https://www.youtube.com/watch?v="):
        return jsonify({
            "success": False,
            "error": "Invalid YouTube URL"
        }), 400

    try:
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]

        chrome_path = next((path for path in chrome_paths if os.path.exists(path)), None)

        if chrome_path:
            subprocess.Popen([chrome_path, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Fallback to the system default browser
            webbrowser.open_new(url)

        print(f"🌐 Opening YouTube in Chrome: {url}")

        return jsonify({
            "success": True,
            "message": "YouTube opened in Chrome",
            "url": url
        })

    except Exception as e:
        print(f"❌ Could not open YouTube: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# MUSIC DATABASE
# ============================================================

music_database = {


    # ========================================================
    # HAPPY
    # ========================================================

    "happy": {

        "english": [

            {
                "title": "Happy",
                "artist": "Pharrell Williams",
                "video_id": "ZbZSe6N_BXs"
            },

            {
                "title": "Can't Stop the Feeling!",
                "artist": "Justin Timberlake",
                "video_id": "ru0K8uYEZWw"
            },

            {
                "title": "On Top of the World",
                "artist": "Imagine Dragons",
                "video_id": "w5tWYmIOWGk"
            }

        ],

        "kannada": [

            {
                "title": "Belageddu",
                "artist": "Kirik Party",
                "video_id": "qQh7c5YhJ3M"
            }

        ],

        "hindi": [

            {
                "title": "Badtameez Dil",
                "artist": "Yeh Jawaani Hai Deewani",
                "video_id": "II2EO3Nw4m0"
            },

            {
                "title": "Gallan Goodiyaan",
                "artist": "Dil Dhadakne Do",
                "video_id": "jCEdTq3j-0U"
            }

        ],

        "tamil": [

            {
                "title": "Arabic Kuthu",
                "artist": "Beast",
                "video_id": "KUN5Uf9mObQ"
            }

        ],

        "telugu": [

            {
                "title": "Butta Bomma",
                "artist": "Ala Vaikunthapurramuloo",
                "video_id": "1Y3XzE3Vq8M"
            }

        ],

        "malayalam": [

            {
                "title": "Jimikki Kammal",
                "artist": "Velipadinte Pusthakam",
                "video_id": "g3Qm0M9Z7Yk"
            }

        ]

    },


    # ========================================================
    # SAD
    # ========================================================

    "sad": {

        "english": [

            {
                "title": "Someone Like You",
                "artist": "Adele",
                "video_id": "hLQl3WQQoQ0"
            },

            {
                "title": "Let Her Go",
                "artist": "Passenger",
                "video_id": "RBumgq5yVrA"
            },

            {
                "title": "Lovely",
                "artist": "Billie Eilish & Khalid",
                "video_id": "V1Pl8CzNzCw"
            }

        ],

        "kannada": [
    {"title": "Anisuthide", "artist": "Mungaru Male", "video_id": "nlsLKA6hlVQ"}
],

        "hindi": [

            {
                "title": "Agar Tum Saath Ho",
                "artist": "Tamasha",
                "video_id": "sK7riqg2mr4"
            },

            {
                "title": "Channa Mereya",
                "artist": "Ae Dil Hai Mushkil",
                "video_id": "284Ov7ysmfA"
            }

        ],

        "tamil": [

            {
                "title": "New York Nagaram",
                "artist": "Sillunu Oru Kadhal",
                "video_id": "5z0M3lJZ6yA"
            }

        ],

        "telugu": [

            {
                "title": "Inkem Inkem Inkem Kaavaale",
                "artist": "Geetha Govindam",
                "video_id": "6xK4n4n1V6A"
            }

        ],

        "malayalam": [

            {
                "title": "Pavizha Mazha",
                "artist": "Athiran",
                "video_id": "rT8w5kJ3y8M"
            }

        ]

    },


    # ========================================================
    # ANGRY
    # ========================================================

    "angry": {

        "english": [

            {
                "title": "Believer",
                "artist": "Imagine Dragons",
                "video_id": "7wtfhZwyrcc"
            },

            {
                "title": "Numb",
                "artist": "Linkin Park",
                "video_id": "kXYiU_JCYtU"
            },

            {
                "title": "Whatever It Takes",
                "artist": "Imagine Dragons",
                "video_id": "gOsM-DYAEhY"
            }

        ],

        "kannada": [

            {
                "title": "Tagaru Banthu Tagaru",
                "artist": "Tagaru",
                "video_id": "Qw2fJ9v0m8M"
            }

        ],

        "hindi": [

            {
                "title": "Apna Time Aayega",
                "artist": "Gully Boy",
                "video_id": "jFGKJBPFdUA"
            }

        ],

        "tamil": [

            {
                "title": "Surviva",
                "artist": "Vivegam",
                "video_id": "2Vv-BfVoq4g"
            }

        ],

        "telugu": [

            {
                "title": "Dhoom Dhaam",
                "artist": "Dasara",
                "video_id": "2v6r3z5V8dA"
            }

        ],

        "malayalam": [

            {
                "title": "Kalippu",
                "artist": "Premam",
                "video_id": "3G5Q7mM0X7Y"
            }

        ]

    },


    # ========================================================
    # NEUTRAL
    # ========================================================

    "neutral": {

        "english": [

            {
                "title": "Blinding Lights",
                "artist": "The Weeknd",
                "video_id": "4NRXx6U8ABQ"
            },

            {
                "title": "Levitating",
                "artist": "Dua Lipa",
                "video_id": "TUVcZfQe-Kw"
            },

            {
                "title": "As It Was",
                "artist": "Harry Styles",
                "video_id": "H5v3kku4y6Q"
            }

        ],

        "kannada": [

            {
                "title": "Kannu Hodiyaka",
                "artist": "Roberrt",
                "video_id": "7m8Q9X3L2VQ"
            }

        ],

        "hindi": [

            {
                "title": "Ilahi",
                "artist": "Yeh Jawaani Hai Deewani",
                "video_id": "fdubeMFwuGs"
            }

        ],

        "tamil": [

            {
                "title": "Megham Karukatha",
                "artist": "Thiruchitrambalam",
                "video_id": "P0W0x3m1yZQ"
            }

        ],

        "telugu": [

            {
                "title": "Samajavaragamana",
                "artist": "Ala Vaikunthapurramuloo",
                "video_id": "OoYQf0b6V6A"
            }

        ],

        "malayalam": [

            {
                "title": "Malare",
                "artist": "Premam",
                "video_id": "GxR0z7M8K9A"
            }

        ]

    },


    # ========================================================
    # FEAR
    # ========================================================

    "fear": {

        "english": [

            {
                "title": "Weightless",
                "artist": "Marconi Union",
                "video_id": "UfcAVejslrU"
            },

            {
                "title": "Calm Down",
                "artist": "Rema",
                "video_id": "WcIcVapfqXw"
            }

        ],

        "kannada": [

            {
                "title": "Anisuthide",
                "artist": "Mungaru Male",
                "video_id": "Z7Q4Yh7Q4VQ"
            }

        ],

        "hindi": [

            {
                "title": "Iktara",
                "artist": "Wake Up Sid",
                "video_id": "fSS_R91Nimw"
            }

        ],

        "tamil": [

            {
                "title": "Munbe Vaa",
                "artist": "Sillunu Oru Kadhal",
                "video_id": "WJ4K0qz5W9M"
            }

        ],

        "telugu": [

            {
                "title": "Inkem Inkem Inkem Kaavaale",
                "artist": "Geetha Govindam",
                "video_id": "6xK4n4n1V6A"
            }

        ],

        "malayalam": [

            {
                "title": "Pavizha Mazha",
                "artist": "Athiran",
                "video_id": "rT8w5kJ3y8M"
            }

        ]

    },


    # ========================================================
    # DISGUST
    # ========================================================

    "disgust": {

        "english": [

            {
                "title": "Good Life",
                "artist": "OneRepublic",
                "video_id": "jZhQOvvV45w"
            },

            {
                "title": "Walking on Sunshine",
                "artist": "Katrina and the Waves",
                "video_id": "iPUmE-tne5U"
            }

        ],

        "kannada": [

            {"title": "Belageddu", "artist": "Kirik Party", "video_id": "ebz20FHrT44"
            }

        ],

        "hindi": [

            {
                "title": "Ilahi",
                "artist": "Yeh Jawaani Hai Deewani",
                "video_id": "fdubeMFwuGs"
            }

        ],

        "tamil": [

            {
                "title": "Vaathi Coming",
                "artist": "Master",
                "video_id": "ObQS5nQKc7Y"
            }

        ],

        "telugu": [

            {
                "title": "Butta Bomma",
                "artist": "Ala Vaikunthapurramuloo",
                "video_id": "1Y3XzE3Vq8M"
            }

        ],

        "malayalam": [

            {
                "title": "Jimikki Kammal",
                "artist": "Velipadinte Pusthakam",
                "video_id": "g3Qm0M9Z7Yk"
            }

        ]

    },


    # ========================================================
    # SURPRISE
    # ========================================================

    "surprise": {

        "english": [

            {
                "title": "Uptown Funk",
                "artist": "Mark Ronson ft. Bruno Mars",
                "video_id": "OPf0YbXqDm0"
            },

            {
                "title": "Dance Monkey",
                "artist": "Tones and I",
                "video_id": "q0hyYWKXF0Q"
            }

        ],

        "kannada": [

            {
                "title": "Dheera Dheera",
                "artist": "KGF",
                "video_id": "Zf4jY7Q5Y5A"
            }

        ],

        "hindi": [

            {
                "title": "Gallan Goodiyaan",
                "artist": "Dil Dhadakne Do",
                "video_id": "jCEdTq3j-0U"
            }

        ],

        "tamil": [

            {
                "title": "Arabic Kuthu",
                "artist": "Beast",
                "video_id": "KUN5Uf9mObQ"
            }

        ],

        "telugu": [

            {
                "title": "Ramuloo Ramulaa",
                "artist": "Ala Vaikunthapurramuloo",
                "video_id": "x7Q3L8M5P2A"
            }

        ],

        "malayalam": [

            {
                "title": "Entammede Jimikki Kammal",
                "artist": "Velipadinte Pusthakam",
                "video_id": "g3Qm0M9Z7Yk"
            }

        ]

    }

}


# ============================================================
# MUSIC RECOMMENDATION API
# ============================================================

# ============================================================
# MUSIC RECOMMENDATION API
# ============================================================

@app.route("/recommendations/<mood>")
def recommendations(mood):

    mood = mood.lower().strip()

    language = request.args.get(
        "language",
        "english"
    ).lower().strip()

    # ----------------------------------------
    # GET MOOD
    # ----------------------------------------

    mood_data = music_database.get(mood)

    if not mood_data:

        return jsonify({
            "success": False,
            "error": f"Mood '{mood}' is not available."
        }), 404

    # ----------------------------------------
    # GET LANGUAGE
    # ----------------------------------------

    recommended_songs = mood_data.get(language)

    if not recommended_songs:

        return jsonify({
            "success": False,
            "mood": mood,
            "language": language,
            "songs": [],
            "error":
                f"No {language} songs available "
                f"for {mood} mood."
        }), 404

    # ----------------------------------------
    # FIND VERIFIED YOUTUBE URLS
    # ----------------------------------------

    songs_with_links = []

    for song in recommended_songs:

        youtube_url = get_youtube_url(
            song["title"],
            song["artist"],
            language
        )

        # Only show songs for which we found
        # a reliable YouTube match.
        if youtube_url:

            songs_with_links.append({

                "title": song["title"],

                "artist": song["artist"],

                "youtube_url": youtube_url

            })

    # ----------------------------------------
    # RETURN RESULTS
    # ----------------------------------------

    return jsonify({

        "success": True,

        "mood": mood,

        "language": language,

        "songs": songs_with_links

    })