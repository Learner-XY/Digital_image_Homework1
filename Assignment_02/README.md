# Assignment 02：Poisson 图像编辑与 Pix2Pix 图像翻译

## 1. 作业简介

本次作业包含两个主要部分：

1. Poisson Image Editing：实现基于泊松融合的图像编辑，将前景区域自然融合到背景图像中；
2. Pix2Pix：实现基于条件生成对抗网络的图像到图像翻译任务。

第一部分主要关注传统图像编辑中的梯度域融合思想，第二部分主要关注深度学习方法在图像翻译任务中的应用。

## 2. 文件结构

```text
Assignment_02/
├── README.md
├── requirements.txt
└── hw_2/
    ├── part1_poisson.py
    ├── part1_gradio_demo.py
    └── part2_pix2pix.py
```

## 3. 环境依赖

建议使用 Python 3.9 或以上版本。安装依赖：

```bash
cd Assignment_02
pip install -r requirements.txt
```

主要依赖包括：

```text
numpy
opencv-python
torch
gradio
```

如果使用 GPU 训练 Pix2Pix，需要根据本机 CUDA 版本安装对应的 PyTorch 版本。

## 4. 运行方式

### 4.1 Poisson 图像融合命令行版本

从 `Assignment_02` 目录运行：

```bash
python hw_2/part1_poisson.py --run-both-examples
```

默认会读取 `base/a1.png` 和 `base/a2.png`，并将结果保存到：

```text
outputs/part1/
```

也可以指定输入图像、输出目录和参数：

```bash
python hw_2/part1_poisson.py \
    --source base/a1.png \
    --target base/a2.png \
    --output-dir outputs/part1 \
    --prefix a1_to_a2 \
    --iterations 1200 \
    --lr 1e-2 \
    --device cpu
```

### 4.2 Poisson 图像融合交互界面

```bash
python hw_2/part1_gradio_demo.py
```

运行后打开 Gradio 界面，操作流程为：

1. 上传前景图和背景图；
2. 在前景图中点击多边形顶点，选择需要融合的区域；
3. 点击 `Close Polygon` 闭合区域；
4. 通过滑块调整前景区域在背景图中的位置；
5. 点击 `Blend`，比较直接复制粘贴和 Poisson 融合的效果。

### 4.3 Pix2Pix 训练

```bash
python hw_2/part2_pix2pix.py train \
    --data-dir base \
    --output-dir outputs/part2 \
    --epochs 10 \
    --batch-size 4 \
    --device cpu
```

如果使用 GPU，可以将参数改为：

```bash
--device cuda
```

训练过程中会输出每个 epoch 的训练损失、验证 L1 损失和 PSNR，并保存中间结果、模型权重和训练历史。

### 4.4 Pix2Pix 预测

训练完成后，可以使用保存的模型进行预测：

```bash
python hw_2/part2_pix2pix.py predict \
    --checkpoint outputs/part2/checkpoints/best.pt \
    --input base/cmp_b0001.png \
    --output outputs/part2/prediction.png \
    --device cpu
```

## 5. 输入和输出

### 5.1 Poisson 图像编辑

输入：

- 前景图像；
- 背景图像；
- 前景图中需要融合区域的多边形点；
- 迭代次数、学习率等参数。

输出：

- 原始前景图；
- 原始背景图；
- 多边形区域可视化图；
- mask 图；
- 直接复制粘贴结果；
- Poisson 融合结果。

### 5.2 Pix2Pix

输入：

- 成对图像数据，例如 `cmp_b*.png` 作为输入图，`cmp_b*.jpg` 作为目标图；
- 训练参数，例如 epoch 数、batch size、学习率等。

输出：

- 训练过程中的损失记录 `train_history.json`；
- 每个 epoch 的可视化样例图；
- 最优模型 `best.pt` 和最终模型 `last.pt`；
- 验证集上的预测结果。

## 6. 方法说明

### 6.1 Poisson Image Editing

Poisson 图像编辑的目标是让融合区域尽量保留前景图像的梯度信息，同时在边界处和背景图像自然衔接。本实现将融合区域看作待优化变量，通过拉普拉斯算子约束前景图和融合图的梯度差异，并用 PyTorch 进行迭代优化。

相比直接复制粘贴，Poisson 融合能够减少边界突兀的问题，使前景区域更自然地融入背景。

### 6.2 Pix2Pix

Pix2Pix 是一种条件生成对抗网络。生成器采用 U-Net 结构，将输入图像映射为目标风格图像；判别器采用 PatchGAN 结构，判断局部图像块是否真实。训练损失由对抗损失和 L1 重建损失共同组成：

1. 对抗损失用于提高生成图像的真实感；
2. L1 损失用于保证生成结果与目标图像在像素层面接近。

## 7. 实验结果与分析

### 7.1 Poisson 图像编辑

实验中，直接复制粘贴通常会在前景和背景交界处产生明显边界，而 Poisson 融合可以减弱边界突兀感，使颜色和纹理过渡更加自然。但当源图和目标图颜色差异较大，或者选区边界不合理时，融合结果仍可能出现颜色偏移。

### 7.2 Pix2Pix

Pix2Pix 可以学习输入图和目标图之间的映射关系。随着训练进行，生成图像通常会逐渐接近目标图像。由于模型规模、训练轮数和数据量有限，生成结果可能仍存在模糊、细节不足或局部结构错误等问题。

## 8. 小结

本次作业分别实现了传统梯度域图像编辑方法和基于深度学习的图像翻译方法。Poisson 图像编辑适合处理局部区域的自然融合，Pix2Pix 则可以从数据中学习复杂的图像映射关系。两类方法分别体现了传统图像处理和深度学习图像生成方法的特点。

## 9. 参考资料

[1] Pérez, P., Gangnet, M., & Blake, A. Poisson Image Editing.  
[2] Isola, P., Zhu, J.-Y., Zhou, T., & Efros, A. A. Image-to-Image Translation with Conditional Adversarial Networks.  
[3] PyTorch 官方文档。  
[4] OpenCV 官方文档。  
[5] Gradio 官方文档。  
[6] 课程资料。