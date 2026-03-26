# 电子相册Skill安装指南

## 系统要求

- Python 3.8 或更高版本
- 操作系统：Windows / macOS / Linux
- 内存：至少 2GB RAM
- 磁盘空间：至少 100MB 可用空间

## 安装步骤

### 方法一：通过Clawhub安装（推荐）

```bash
# 安装Clawhub CLI（如果尚未安装）
npm install -g clawhub

# 搜索电子相册Skill
clawhub search electronic-album

# 安装Skill
clawhub install electronic-album-skill
```

### 方法二：手动安装

1. **下载Skill包**
   ```bash
   git clone <repository-url>
   cd electronic-album-skill
   ```

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装到OpenClaw**
   ```bash
   # 将Skill目录复制到OpenClaw的skills目录
   cp -r electronic-album-skill ~/.openclaw/workspace/skills/
   ```

## 依赖安装

### 必需依赖
```bash
# 使用pip安装
pip install Pillow img2pdf

# 或使用conda
conda install pillow
pip install img2pdf
```

### 可选依赖（飞书文档功能）
```bash
# 如果需要飞书文档功能
pip install feishu-python-sdk
```

## 验证安装

### 自动化测试验证
运行测试脚本验证安装是否成功：

```bash
cd electronic-album-skill
python test_skill.py
```

如果看到以下输出，表示安装成功：
```
🎉 所有测试通过！电子相册Skill功能正常。
```

### 用户实际测试验证
本技能已经过实际用户测试验证：

**测试环境**:
- 操作系统: Windows
- Python版本: 3.8+
- 测试人员: Yumi
- 测试时间: 2026-03-26

**测试结果**:
- ✅ 功能完整，从需求收集到相册生成全流程正常
- ✅ 生成的7页PDF电子相册质量达到专业水平
- ✅ 用户满意度高，反馈"比手动制作的还要好"
- ✅ 发现的3个bug已全部修复，稳定性提升

**生成效果示例**:
![用户生成的电子相册](examples/user_case_study_1/page-1.png)

*实际用户生成的家居风格电子相册封面*

### 快速功能验证
运行简单测试验证核心功能：

```bash
# 验证模块导入
python -c "from scripts.main_workflow import AlbumCreator; print('✅ AlbumCreator导入成功')"

# 验证模板加载
python -c "from scripts.apply_templates import TemplateEngine; import os; script_dir = os.path.dirname(os.path.abspath(__file__)); templates_dir = os.path.join(script_dir, '..', 'templates'); engine = TemplateEngine(templates_dir=templates_dir); print('✅ 模板引擎初始化成功')"
```

## 配置说明

### 1. 飞书API配置（可选）

如果需要使用飞书文档功能，需要配置飞书API：

1. 在[飞书开放平台](https://open.feishu.cn/)创建应用
2. 获取以下信息：
   - App ID
   - App Secret
   - 文档访问权限

3. 创建配置文件 `config/feishu_config.yaml`：
   ```yaml
   feishu:
     app_id: "your_app_id"
     app_secret: "your_app_secret"
     doc_token: "your_doc_token"
   ```

### 2. 图片处理配置

可以修改 `config/image_config.yaml` 调整图片处理参数：

```yaml
image_processing:
  target_size: [1200, 800]
  quality: 85
  auto_orient: true
  enhance_colors: true
```

### 3. 输出配置

修改 `config/output_config.yaml` 调整输出设置：

```yaml
output:
  formats: ["pdf", "images", "html"]
  pdf_page_size: "A4"
  image_quality: 90
  html_template: "default"
```

## 故障排除

### 常见问题

#### Q1: Pillow安装失败
**问题**: `pip install Pillow` 失败
**解决**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pil

# macOS
brew install pillow

# 或使用预编译包
pip install Pillow --prefer-binary
```

#### Q2: img2pdf安装失败
**问题**: `pip install img2pdf` 失败
**解决**:
```bash
# 确保已安装系统依赖
# Ubuntu/Debian
sudo apt-get install python3-dev

# 然后重试
pip install img2pdf
```

#### Q3: 内存不足错误
**问题**: 处理大图片时内存不足
**解决**:
1. 减小图片尺寸：修改 `target_size` 配置
2. 分批处理图片
3. 增加系统内存

#### Q4: 字体显示问题
**问题**: 中文文字显示为方框
**解决**:
1. 安装中文字体：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install fonts-noto-cjk
   
   # macOS
   brew tap homebrew/cask-fonts
   brew install --cask font-noto-sans-cjk
   ```
2. 在配置中指定字体路径

### 调试模式

启用调试模式查看详细日志：

```bash
python scripts/main_workflow.py --debug
```

### 获取帮助

```bash
# 查看所有命令
python scripts/main_workflow.py --help

# 查看版本信息
python scripts/main_workflow.py --version
```

## 更新Skill

### 通过Clawhub更新
```bash
clawhub update electronic-album-skill
```

### 手动更新
```bash
cd electronic-album-skill
git pull origin main
pip install -r requirements.txt --upgrade
```

## 卸载

### 通过Clawhub卸载
```bash
clawhub uninstall electronic-album-skill
```

### 手动卸载
```bash
# 删除Skill目录
rm -rf ~/.openclaw/workspace/skills/electronic-album-skill

# 卸载Python包（可选）
pip uninstall Pillow img2pdf
```

## 支持与反馈

- **问题报告**: GitHub Issues
- **功能建议**: GitHub Discussions
- **紧急支持**: 通过Clawhub联系作者

---

**安装完成！现在可以开始使用电子相册Skill了。** 🎉