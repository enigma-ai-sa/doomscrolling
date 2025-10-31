from flask import Flask, request, jsonify
import time
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import base64
from flask_cors import CORS
import boto3

load_dotenv()
app = Flask(__name__)
CORS(app) 

PROMPT = "Make the person(s) perform a backflip and then pull out the enigma logo from behind their backs."

@app.route("/generate-video", methods=["POST"])
def generate_video():
    print("endpoint hit")
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
                negative_prompt="low quality, distorted, unrealistic",
                aspect_ratio="16:9",
                reference_images=[uploaded_reference, root_reference],
            ),
        )

        # --- 4️⃣ Poll operation until video is ready ---
        while not operation.done:
            print("⏳ Waiting for video generation...")
            time.sleep(10)
            operation = client.operations.get(operation)

        # --- 5️⃣ Download and save ---
        # generate unique filename using timestamp
        filename = f"{time.time()}.mp4"
        s3Key = f"testingEnviroment/{filename}"
        video = operation.response.generated_videos[0]
        client.files.download(file=video.video)
        video.video.save(filename)

        # --- 6️⃣ Upload video to S3 bucket ---
        s3 = boto3.client('s3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        # bucket name is from .env
        bucket_name = os.getenv("S3_BUCKET")
        s3.upload_file(filename, bucket_name, s3Key)

        # --- 7️⃣ Delete local video file ---
        os.remove(filename)

        # --- 8️⃣ Return video URL ---
        return jsonify({"message": "✅ Video generated successfully", "video_url": f"https://{bucket_name}.s3.{os.getenv("AWS_REGION")}.amazonaws.com/{s3Key}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get-videos", methods=["GET"])
def get_videos():
    try:
        # get all videos from s3 bucket
        s3 = boto3.client('s3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        bucket_name = os.getenv("S3_BUCKET")
        aws_region = os.getenv("AWS_REGION")
        
        # Handle pagination to get all objects
        video_urls = []
        continuation_token = None
        
        while True:
            if continuation_token:
                response = s3.list_objects_v2(
                    Bucket=bucket_name, 
                    Prefix="testingEnviroment/",
                    ContinuationToken=continuation_token
                )
            else:
                response = s3.list_objects_v2(
                    Bucket=bucket_name, 
                    Prefix="testingEnviroment/"
                )
            
            # Get videos from this batch
            videos = response.get('Contents', [])
            for video in videos:
                video_urls.append(f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{video['Key']}")
            
            # Check if there are more results
            if response.get('IsTruncated'):
                continuation_token = response.get('NextContinuationToken')
            else:
                break
        
        return jsonify({"videos": video_urls})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
