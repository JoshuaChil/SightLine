
def generate_llm_prompt(boxes, classes, depth, class_names):
    detected_objects_info = []

    for box, cls in zip(boxes, classes):
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        
        class_name = class_names[int(cls)]  # map class ID to name
        
        # Ensure center coordinates are within depth map bounds
        cx = max(0, min(cx, depth.shape[1] - 1))
        cy = max(0, min(cy, depth.shape[0] - 1))
        
        depth_at_center = depth[cy, cx].item()

        detected_objects_info.append(f"- A {class_name} located at approximate coordinates ({cx}, {cy}) with an estimated depth of {depth_at_center:.2f} meters.")

    if detected_objects_info:
        prompt = "Based on the visual analysis of the environment, the following objects are present:\n"
        prompt += "\n".join(detected_objects_info)
        prompt += "\nThese are all the objects in front of a blind person, and their approximate distances from them. The persons eyes are located at the center of the image. In only 1 sentence, answer the question the user has to help them navigate their environment since they cannot see. Never state co-ordinates, but use them to help guide the user regarding relative object location. The user's eyes are located at coordinate  "
        prompt += "\n\nQuestion: "
    else:
        prompt = "No distinct objects were detected in the environment, indicating a potentially clear or unpopulated scene."
    
    return prompt