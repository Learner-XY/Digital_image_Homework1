# 运行时可能因 gradio 与 huggingface_hub 版本不兼容导致 ImportError。
# 如果出现错误，请通过命令行运行：
#   pip install -U gradio huggingface_hub
# 或者降级 huggingface_hub 至 0.17.x：
#   pip install "huggingface_hub<0.18"

try:
    import gradio as gr
except ImportError as e:
    raise ImportError(
        "无法导入 gradio，请确保安装了兼容版本的 gradio 和 huggingface_hub。\n"
        "使用 pip 安装：pip install -U gradio huggingface_hub 或 pip install \"huggingface_hub<0.18\""
    ) from e

import cv2
import numpy as np

# Function to convert 2x3 affine matrix to 3x3 for matrix multiplication
def to_3x3(affine_matrix):
    return np.vstack([affine_matrix, [0, 0, 1]])

# Function to apply transformations based on user inputs
def apply_transform(image, scale, rotation, translation_x, translation_y, flip_horizontal):

    # Convert the image from PIL format to a NumPy array
    image = np.array(image)
    # Pad the image to avoid boundary issues
    pad_size = min(image.shape[0], image.shape[1]) // 2
    image_new = np.zeros((pad_size*2+image.shape[0], pad_size*2+image.shape[1], 3), dtype=np.uint8) + np.array((255,255,255), dtype=np.uint8).reshape(1,1,3)
    image_new[pad_size:pad_size+image.shape[0], pad_size:pad_size+image.shape[1]] = image
    image = np.array(image_new)
    transformed_image = np.array(image)

    # Get image dimensions
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    # Get rotation and scale matrix around center
    M_rs = cv2.getRotationMatrix2D(center, rotation, scale)

    # Add translation
    M_rs[0, 2] += translation_x
    M_rs[1, 2] += translation_y

    # Convert to 3x3
    M = to_3x3(M_rs)

    # If flip horizontal, apply flip matrix
    if flip_horizontal:
        M_flip = np.array([[-1, 0, w], [0, 1, 0], [0, 0, 1]])
        M = M_flip @ M

    # Apply transformation
    transformed_image = cv2.warpAffine(image, M[:2], (w, h), borderValue=(255, 255, 255))

    return transformed_image

# Gradio Interface
def interactive_transform():
    with gr.Blocks() as demo:
        gr.Markdown("## Image Transformation Playground")
        
        # Define the layout
        with gr.Row():
            # Left: Image input and sliders
            with gr.Column():
                image_input = gr.Image( type="pil", label="Upload Image")

                scale = gr.Slider(minimum=0.1, maximum=2.0, step=0.1, value=1.0, label="Scale")
                rotation = gr.Slider(minimum=-180, maximum=180, step=1, value=0, label="Rotation (degrees)")
                translation_x = gr.Slider(minimum=-300, maximum=300, step=10, value=0, label="Translation X")
                translation_y = gr.Slider(minimum=-300, maximum=300, step=10, value=0, label="Translation Y")
                flip_horizontal = gr.Checkbox(label="Flip Horizontal")
            
            # Right: Output image
            image_output = gr.Image(label="Transformed Image")
        
        # Automatically update the output when any slider or checkbox is changed
        inputs = [
            image_input, scale, rotation, 
            translation_x, translation_y, 
            flip_horizontal
        ]

        # Link inputs to the transformation function
        image_input.change(apply_transform, inputs, image_output)
        scale.change(apply_transform, inputs, image_output)
        rotation.change(apply_transform, inputs, image_output)
        translation_x.change(apply_transform, inputs, image_output)
        translation_y.change(apply_transform, inputs, image_output)
        flip_horizontal.change(apply_transform, inputs, image_output)

    return demo

# Launch the Gradio interface
# 如果本地 localhost 无法访问，可通过 share=True 生成公共链接
interactive_transform().launch(share=True)
