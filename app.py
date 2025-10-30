from flask import Flask, request, jsonify
import time
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import base64
from flask_cors import CORS

load_dotenv()
app = Flask(__name__)
CORS(app) 

PROMPT = "Make the person(s) in the video take a step back and pull out the enigma logo from behind their backs"

@app.route("/generate-video", methods=["POST"])
def generate_video():
    try:
        # initialize google veo
        client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        # --- 1️⃣ Handle the uploaded PNG image ---
        if "image" not in request.files:
            return jsonify({"error": "Missing 'image' file"}), 400

        uploaded_file = request.files["image"]
        uploaded_bytes = base64.b64encode(uploaded_file.read()).decode("utf-8")

        uploaded_reference = types.VideoGenerationReferenceImage(
            image={"imageBytes": uploaded_bytes, "mimeType": "image/png"},
            reference_type="asset",
        )

        # --- 2️⃣ Add your fixed local reference image ---
        with open("enigma_logo.png", "rb") as f:
            root_bytes = base64.b64encode(f.read()).decode("utf-8")

        root_reference = types.VideoGenerationReferenceImage(
            image={"imageBytes": root_bytes, "mimeType": "image/png"},
            reference_type="asset",
        )
        print("Generating video...")
        # --- 3️⃣ Generate video with both images ---
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=PROMPT,
            config=types.GenerateVideosConfig(
                reference_images=[uploaded_reference, root_reference],
            ),
        )

        # --- 4️⃣ Poll operation until video is ready ---
        while not operation.done:
            print("⏳ Waiting for video generation...")
            time.sleep(10)
            operation = client.operations.get(operation)

        # --- 5️⃣ Download and save ---
        video = operation.response.generated_videos[0]
        client.files.download(file=video.video)
        video.video.save("generated_video.mp4")

        return jsonify({"message": "✅ Video generated successfully", "file": "generated_video.mp4"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    

if __name__ == "__main__":
    app.run(debug=True)
