# electronic-album-skill

## 概述
电子相册自动生成技能，帮助用户快速将照片制作成精美的电子相册。支持多种排版模板、自动图片处理、飞书文档预览和PDF生成。

## 功能特性

### 🎯 核心功能
1. **智能需求收集** - 交互式收集用户相册需求
2. **批量图片处理** - 自动调整尺寸、色彩、方向
3. **多样化模板** - 6种基础排版模板
4. **自动化排版** - 根据需求自动应用模板
5. **多格式输出** - 飞书文档预览 + PDF生成
6. **易于扩展** - 模块化设计，支持自定义模板

### 📋 工作流程
```
用户交互 → 需求分析 → 图片处理 → 模板应用 → 相册生成 → 输出交付
```

## 快速开始

### 安装
```bash
# 通过Clawhub安装
clawhub install electronic-album-skill

# 或手动安装
git clone <repository-url>
cd electronic-album-skill
```

### 基本使用
```python
from electronic_album import AlbumCreator

# 创建相册生成器
creator = AlbumCreator()

# 设置基本参数
creator.set_images(["image1.jpg", "image2.jpg", "image3.jpg"])
creator.set_layout_preference("mixed")  # 混合排版
creator.set_style("elegant")  # 优雅风格

# 生成相册
album = creator.generate()

# 输出结果
album.preview_in_feishu()  # 飞书文档预览
album.export_pdf("my_album.pdf")  # 导出PDF
```

## 详细使用指南

### 1. 需求收集模块
收集用户对相册的具体需求：

#### 必需信息
- **图片数量**: 相册包含的照片数量
- **排版偏好**: 单张、两张、三张、四张或混合排版
- **风格选择**: 简约、文艺、商务、活泼等
- **文字需求**: 是否需要文字说明，文字量多少

#### 可选信息
- **主题颜色**: 相册的主色调
- **字体偏好**: 中文字体选择
- **特殊要求**: 自定义需求

### 2. 图片处理模块
自动处理用户提供的图片：

#### 处理功能
- **尺寸统一**: 自动调整图片尺寸
- **色彩优化**: 亮度、对比度、饱和度调整
- **方向校正**: 自动识别和校正图片方向
- **格式转换**: 支持多种图片格式
- **质量压缩**: 优化文件大小，保持画质

#### 批量处理
```python
from electronic_album.processor import ImageProcessor

processor = ImageProcessor()
processed_images = processor.batch_process(
    image_paths,
    target_size=(1200, 800),
    quality=85
)
```

### 3. 模板应用模块
根据需求选择合适的模板并应用：

#### 可用模板
| 模板类型 | 文件 | 适用场景 |
|---------|------|----------|
| 封面模板 | `01_cover.jpg` | 相册封面 |
| 目录模板 | `02_directory.jpg` | 章节分隔页 |
| 单张模板 | `03_single_image.jpg` | 突出重要照片 |
| 两张模板 | `04_two_images.jpg` | 对比展示 |
| 三张模板 | `05_three_images.jpg` | 系列展示 |
| 四张模板 | `06_four_images.md` | 多图集锦 |

#### 模板选择逻辑
```python
# 根据图片数量和用户偏好选择模板
def select_template(image_count, user_preference):
    if image_count == 1:
        return "single"
    elif image_count == 2:
        return "two_images"
    elif image_count == 3:
        return "three_images"
    elif image_count == 4:
        return "four_images"
    else:
        return user_preference  # 使用用户指定的偏好
```

### 4. 相册生成模块
将处理后的图片应用到模板，生成完整相册：

#### 生成步骤
1. **封面生成** - 使用封面模板创建相册封面
2. **目录生成** - 根据章节结构生成目录页
3. **内容页生成** - 按顺序应用内容模板
4. **封底生成** - 创建相册封底
5. **页面排序** - 按逻辑顺序排列所有页面

#### 页面布局示例
```python
# 生成单张图片页面
page = template_engine.apply_single_template(
    image=processed_image,
    template="03_single_image.jpg",
    caption="美好的回忆"
)

# 生成多张图片页面
page = template_engine.apply_multi_template(
    images=[img1, img2, img3],
    template="05_three_images.jpg",
    layout="grid"
)
```

### 5. 输出生成模块
生成多种格式的输出文件：

#### 飞书文档输出
- **实时预览**: 在飞书文档中实时查看相册
- **交互式编辑**: 支持在线调整和编辑
- **分享便捷**: 一键分享给他人

#### PDF输出
- **高质量打印**: 适合打印成实体相册
- **跨平台查看**: 在任何设备上查看
- **永久保存**: 长期保存和归档

#### 其他输出格式
- **图片集合**: 所有页面单独保存为图片
- **HTML预览**: 网页版相册预览
- **社交媒体格式**: 适配社交媒体的版本

## 配置选项

### 基本配置
```yaml
# config.yaml
album:
  page_size: "A4"  # 页面尺寸
  orientation: "portrait"  # 方向：portrait/landscape
  quality: "high"  # 输出质量：low/medium/high
  
templates:
  default_style: "elegant"
  enable_custom_templates: true
  
output:
  formats: ["feishu", "pdf", "images"]
  feishu_doc_token: "your_doc_token"
```

### 高级配置
```yaml
processing:
  auto_orient: true
  resize_strategy: "fit"
  compression_level: 80
  
fonts:
  chinese: "NotoSansCJK-Regular"
  english: "Arial"
  
colors:
  primary: "#1E90FF"
  secondary: "#FF6B6B"
  background: "#FFFFFF"
```

## 扩展开发

### 自定义模板
1. 在`templates/custom/`目录中添加新模板
2. 更新`templates/template_index.md`注册新模板
3. 实现对应的模板应用逻辑

### 插件系统
```python
# 自定义处理器插件
from electronic_album.plugins import BaseProcessor

class CustomProcessor(BaseProcessor):
    def process(self, image):
        # 自定义处理逻辑
        return enhanced_image

# 注册插件
album_creator.register_processor(CustomProcessor())
```

### API扩展
```python
# RESTful API
from electronic_album.api import create_app

app = create_app()

# 启动服务
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

## 故障排除

### 常见问题

#### Q1: 图片处理失败
**问题**: 图片无法正常处理
**解决**:
1. 检查图片格式是否支持（支持JPG、PNG、WEBP）
2. 检查图片文件是否损坏
3. 调整处理参数（尺寸、质量等）

#### Q2: 模板应用异常
**问题**: 图片在模板中显示不正常
**解决**:
1. 检查图片尺寸是否与模板匹配
2. 调整图片裁剪策略
3. 检查模板文件是否完整

#### Q3: 飞书文档上传失败
**问题**: 无法上传到飞书文档
**解决**:
1. 检查飞书API token是否有效
2. 检查网络连接
3. 确认文档权限设置

#### Q4: PDF生成质量差
**问题**: PDF文件质量不佳
**解决**:
1. 提高输出质量设置
2. 使用更高分辨率的原始图片
3. 调整PDF压缩参数

### 调试模式
```python
# 启用调试模式
creator = AlbumCreator(debug=True)

# 查看详细日志
creator.set_log_level("DEBUG")
```

## 性能优化

### 内存优化
- 流式处理大图片
- 及时释放不再使用的资源
- 使用缓存减少重复处理

### 速度优化
- 并行处理多张图片
- 使用更高效的图像处理库
- 预加载常用模板

### 质量优化
- 智能选择处理参数
- 保持原始图片质量
- 自适应输出格式

## 版本历史

### v1.0.0 (计划中)
- 基础相册生成功能
- 6种基础模板
- 飞书文档和PDF输出
- 基本图片处理

### v1.1.0 (规划中)
- 更多模板类型
- 高级图片处理功能
- 自定义模板支持
- 性能优化

### v1.2.0 (规划中)
- 插件系统
- API接口
- 云端处理支持
- 移动端优化

## 贡献指南

### 开发环境设置
```bash
# 克隆仓库
git clone <repository-url>
cd electronic-album-skill

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/
```

### 代码规范
- 遵循PEP 8编码规范
- 添加类型注解
- 编写单元测试
- 更新文档

### 提交贡献
1. Fork仓库
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证
MIT License

## 支持与联系
- 问题反馈: GitHub Issues
- 功能建议: GitHub Discussions
- 紧急支持: 通过Clawhub联系

---

**电子相册，让美好记忆更易珍藏** 📸✨