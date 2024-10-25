import torch
from diffusers import StableDiffusionPipeline
model_id = "SG161222/Realistic_Vision_V2.0"

pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
pipeline = pipeline.to("cuda")

prompt = "residential area"
negative_prompt = "sketch, cartoon, drawing, anime, extra limbs, extra arms, \
			extra legs, malformed limbs"

image = pipeline(prompt, negative_prompt=negative_prompt, guidance_scale=7.5, \
			num_inference_steps=50, height=512, width=512).images[0]
image.save("./tmp3/0.jpg")
image
