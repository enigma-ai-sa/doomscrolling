APPROACH 2 (end the video with a certain frame):
        # operation = client.models.generate_videos(
        #     model="veo-3.1-generate-preview",
        #     prompt=PROMPT,
        #     config=types.GenerateVideosConfig(
        #         negative_prompt="low quality, distorted, unrealistic, deformed body, distorted limbs, unnatural movement, body disfigurement, inverted anatomy, warped perspective",
        #         resolution="720p",
        #         last_frame={
        #             "imageBytes": root_bytes,
        #             "mimeType": "image/png"
        #         }
        #     ),
        #     image={
        #         "imageBytes": uploaded_bytes,
        #         "mimeType": "image/jpeg"
        #     }
        # )