# Assignment 01：图像几何变换与图像形变

## 1. 作业简介

本次作业主要实现图像几何变换与基于控制点的图像形变。代码分为两个部分：

1. 全局几何变换：对图像进行缩放、旋转、平移和水平翻转；
2. 控制点图像形变：用户在图像上选择源点和目标点，程序根据控制点对图像进行 MLS 形变。

其中，控制点形变部分使用 Moving Least Squares 方法，根据用户指定的点对计算每个像素的映射位置，从而得到较平滑的图像变形结果。

## 2. 文件结构

```text
Assignment_01/
├── README.md
├── requirements.txt
└── code/
    ├── run_global_transform.py
    ├── run_point_transform.py
    └── test.py

01_ImageWarping/
└── pics/
    ├── teaser.png
    ├── global_demo.gif
    └── point_demo.gif
```

说明：`pics` 文件夹中的图片和 GIF 是本次作业的实验结果展示。当前 GitHub 工具不方便直接批量移动 GIF/PNG 二进制文件，因此结果图暂时仍保留在原来的 `01_ImageWarping/pics/` 目录下，并在本报告中直接引用。

## 3. 环境依赖

建议使用 Python 3.9 或以上版本。安装依赖：

```bash
cd Assignment_01
pip install -r requirements.txt
```

依赖主要包括：

```text
numpy
opencv-python
gradio
```

如果运行 Gradio 时出现版本兼容问题，可以尝试：

```bash
pip install -U gradio huggingface_hub
```

或：

```bash
pip install "huggingface_hub<0.18"
```

## 4. 运行方式

从 `Assignment_01` 目录运行：

### 4.1 全局几何变换

```bash
python code/run_global_transform.py
```

运行后会启动 Gradio 网页界面。用户可以上传图像，并通过滑块调整缩放、旋转、平移和水平翻转参数。

### 4.2 基于控制点的图像形变

```bash
python code/run_point_transform.py
```

运行后会启动 Gradio 网页界面。操作步骤如下：

1. 上传一张图像；
2. 在图像中按照“源点 → 目标点”的顺序点击控制点；
3. 如果希望添加固定点，可以在同一位置连续点击两次；
4. 点击 `Run Warping` 得到图像形变结果；
5. 点击 `Clear Points` 可以清空控制点并重新选择。

### 4.3 测试依赖版本

```bash
python code/test.py
```

该脚本用于输出当前环境中 `gradio`、`opencv-python` 和 `numpy` 的版本信息。

## 5. 输入和输出

### 输入

- 一张 RGB 图像；
- 全局变换参数，例如缩放比例、旋转角度、平移距离和是否水平翻转；
- 或者若干组源控制点和目标控制点。

### 输出

- 全局几何变换后的图像；
- MLS 控制点形变后的图像；
- Gradio 网页界面中的可视化结果；
- 实验展示 GIF，保存在 `01_ImageWarping/pics/` 中。

## 6. 方法说明

### 6.1 全局几何变换

全局几何变换通过仿射变换矩阵实现。程序利用 OpenCV 中的旋转缩放矩阵，并进一步叠加平移和翻转操作，最后通过 `cv2.warpAffine` 对图像进行重采样。

### 6.2 MLS 图像形变

MLS 方法的核心思想是：对于输出图像中的每个像素，根据它到目标控制点的距离计算权重，再由这些权重确定局部仿射变换。这样可以让用户指定的控制点尽量满足源点到目标点的对应关系，同时保持图像整体变形较平滑。

为了减少边界区域出现明显拉伸或塌陷，程序中额外加入了若干边界固定点，使边界区域更加稳定。

## 7. 实验结果与分析

### 7.1 总体展示

![teaser](../01_ImageWarping/pics/teaser.png)

### 7.2 全局几何变换结果

![global_demo](../01_ImageWarping/pics/global_demo.gif)

### 7.3 控制点图像形变结果

![point_demo](../01_ImageWarping/pics/point_demo.gif)

实验表明：

1. 全局几何变换可以正确完成图像缩放、旋转、平移和翻转；
2. 控制点较少时，MLS 形变整体较平滑，适合进行大范围变形；
3. 控制点集中在局部区域时，局部形变更加明显，但也可能出现一定的局部拉伸；
4. 加入边界固定点后，图像边缘区域更稳定，不容易出现严重塌陷。

## 8. 小结

本次作业完成了图像全局几何变换和基于 MLS 的交互式图像形变。通过 Gradio 界面，用户可以直观地上传图像、选择控制点并观察形变结果。该方法实现简单，交互性较好，但当控制点分布过于稀疏或形变幅度过大时，仍可能出现局部失真。

## 9. 参考资料

[1] Schaefer, S., McPhail, T., & Warren, J. Image Deformation Using Moving Least Squares.  
[2] OpenCV 官方文档。  
[3] Gradio 官方文档。  
[4] 课程资料。