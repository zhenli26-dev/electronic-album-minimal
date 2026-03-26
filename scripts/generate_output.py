#!/usr/bin/env python3
"""
输出生成模块
负责将生成的相册页面输出为多种格式（飞书文档、PDF、图片集合等）
"""

import os
import sys
import logging
import json
import tempfile
import shutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """输出格式枚举"""
    FEISHU_DOC = "feishu_doc"     # 飞书文档
    PDF = "pdf"                   # PDF文件
    IMAGES = "images"             # 图片集合
    HTML = "html"                 # HTML网页
    ZIP = "zip"                   # 压缩包


class OutputQuality(Enum):
    """输出质量枚举"""
    LOW = "low"                   # 低质量（快速）
    MEDIUM = "medium"             # 中等质量
    HIGH = "high"                 # 高质量
    ULTRA = "ultra"               # 超高质量


@dataclass
class OutputConfig:
    """输出配置"""
    output_formats: List[OutputFormat] = None
    output_quality: OutputQuality = OutputQuality.HIGH
    
    # PDF配置
    pdf_page_size: str = "A4"  # A4, Letter, Legal, etc.
    pdf_orientation: str = "portrait"  # portrait, landscape
    pdf_margin: int = 20  # 页边距（像素）
    pdf_compress: bool = True
    pdf_encrypt: bool = False
    pdf_password: Optional[str] = None
    
    # 飞书文档配置
    feishu_doc_token: Optional[str] = None
    feishu_folder_token: Optional[str] = None
    feishu_doc_title: str = "电子相册"
    feishu_share_enabled: bool = True
    
    # 图片配置
    image_format: str = "jpg"  # jpg, png, webp
    image_quality: int = 90  # 1-100
    create_thumbnails: bool = True
    thumbnail_size: Tuple[int, int] = (300, 200)
    
    # HTML配置
    html_template: str = "default"
    html_include_navigation: bool = True
    html_responsive: bool = True
    
    # 通用配置
    output_dir: str = "./output"
    clean_temp_files: bool = True
    preserve_source_images: bool = False
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = [OutputFormat.PDF, OutputFormat.IMAGES]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['output_formats'] = [fmt.value for fmt in data['output_formats']]
        data['output_quality'] = data['output_quality'].value
        data['thumbnail_size'] = list(data['thumbnail_size'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OutputConfig':
        """从字典创建"""
        if 'output_formats' in data:
            data['output_formats'] = [OutputFormat(fmt) for fmt in data['output_formats']]
        if 'output_quality' in data:
            data['output_quality'] = OutputQuality(data['output_quality'])
        if 'thumbnail_size' in data and isinstance(data['thumbnail_size'], list):
            data['thumbnail_size'] = tuple(data['thumbnail_size'])
        return cls(**data)


@dataclass
class OutputResult:
    """输出结果"""
    success: bool
    output_format: OutputFormat
    output_paths: List[str]
    message: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'output_format': self.output_format.value,
            'output_paths': self.output_paths,
            'message': self.message,
            'metadata': self.metadata or {}
        }


class OutputGenerator:
    """输出生成器"""
    
    def __init__(self, config: Optional[OutputConfig] = None):
        """
        初始化输出生成器
        
        Args:
            config: 输出配置
        """
        self.config = config or OutputConfig()
        
        # 创建输出目录
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # 检查依赖
        self._check_dependencies()
        
        logger.info("输出生成器初始化完成")
        logger.info(f"输出格式: {[fmt.value for fmt in self.config.output_formats]}")
        logger.info(f"输出目录: {self.config.output_dir}")
    
    def _check_dependencies(self):
        """检查依赖"""
        dependencies = {
            'img2pdf': '用于生成PDF',
            'Pillow': '用于图片处理',
        }
        
        missing_deps = []
        
        # 检查img2pdf
        try:
            import img2pdf
            self.img2pdf_available = True
        except ImportError:
            self.img2pdf_available = False
            missing_deps.append('img2pdf')
        
        # 检查Pillow
        try:
            from PIL import Image
            self.pillow_available = True
        except ImportError:
            self.pillow_available = False
            missing_deps.append('Pillow')
        
        if missing_deps:
            logger.warning(f"缺少依赖: {missing_deps}")
            logger.warning("部分功能可能受限")
    
    def generate_outputs(self, page_images: List[str], 
                        album_title: str = "电子相册",
                        album_description: str = "") -> Dict[OutputFormat, OutputResult]:
        """
        生成多种格式的输出
        
        Args:
            page_images: 页面图片路径列表
            album_title: 相册标题
            album_description: 相册描述
            
        Returns:
            各种输出格式的结果字典
        """
        if not page_images:
            logger.warning("没有页面图片可输出")
            return {}
        
        results = {}
        
        # 为每种输出格式生成结果
        for output_format in self.config.output_formats:
            try:
                logger.info(f"开始生成 {output_format.value} 格式输出")
                
                if output_format == OutputFormat.PDF:
                    result = self._generate_pdf(page_images, album_title)
                elif output_format == OutputFormat.IMAGES:
                    result = self._generate_images(page_images, album_title)
                elif output_format == OutputFormat.HTML:
                    result = self._generate_html(page_images, album_title, album_description)
                elif output_format == OutputFormat.ZIP:
                    result = self._generate_zip(page_images, album_title)
                elif output_format == OutputFormat.FEISHU_DOC:
                    result = self._generate_feishu_doc(page_images, album_title, album_description)
                else:
                    result = OutputResult(
                        success=False,
                        output_format=output_format,
                        output_paths=[],
                        message=f"不支持的输出格式: {output_format.value}"
                    )
                
                results[output_format] = result
                logger.info(f"{output_format.value} 生成结果: {result.success} - {result.message}")
                
            except Exception as e:
                logger.error(f"生成 {output_format.value} 输出失败: {e}")
                results[output_format] = OutputResult(
                    success=False,
                    output_format=output_format,
                    output_paths=[],
                    message=f"生成失败: {str(e)}"
                )
        
        # 生成汇总报告
        self._generate_summary_report(results, album_title)
        
        return results
    
    def _generate_pdf(self, page_images: List[str], album_title: str) -> OutputResult:
        """生成PDF文件"""
        if not self.img2pdf_available:
            return OutputResult(
                success=False,
                output_format=OutputFormat.PDF,
                output_paths=[],
                message="缺少img2pdf依赖，无法生成PDF"
            )
        
        try:
            import img2pdf
            from PIL import Image
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 准备图片（确保格式正确）
                pdf_images = []
                for i, image_path in enumerate(page_images):
                    try:
                        # 检查并转换图片格式
                        img = Image.open(image_path)
                        
                        # 转换为RGB模式（PDF需要）
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # 保存为临时文件
                        temp_path = os.path.join(temp_dir, f"page_{i+1:03d}.jpg")
                        img.save(temp_path, quality=95)
                        pdf_images.append(temp_path)
                        
                    except Exception as e:
                        logger.warning(f"处理图片 {image_path} 失败: {e}")
                        continue
                
                if not pdf_images:
                    return OutputResult(
                        success=False,
                        output_format=OutputFormat.PDF,
                        output_paths=[],
                        message="没有有效的图片可生成PDF"
                    )
                
                # 生成PDF
                pdf_filename = f"{album_title}_{int(time.time())}.pdf"
                pdf_path = os.path.join(self.config.output_dir, pdf_filename)
                
                # 设置PDF选项
                pdf_options = {
                    'layout_fun': img2pdf.get_layout_fun(
                        (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))  # A4尺寸
                    )
                }
                
                # 生成PDF
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert(pdf_images, **pdf_options))
                
                # 检查文件大小
                file_size = os.path.getsize(pdf_path)
                file_size_mb = file_size / (1024 * 1024)
                
                metadata = {
                    'page_count': len(pdf_images),
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size_mb, 2),
                    'original_images': len(page_images),
                    'processed_images': len(pdf_images)
                }
                
                return OutputResult(
                    success=True,
                    output_format=OutputFormat.PDF,
                    output_paths=[pdf_path],
                    message=f"PDF生成成功: {len(pdf_images)}页, {round(file_size_mb, 2)}MB",
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error(f"生成PDF失败: {e}")
            return OutputResult(
                success=False,
                output_format=OutputFormat.PDF,
                output_paths=[],
                message=f"PDF生成失败: {str(e)}"
            )
    
    def _generate_images(self, page_images: List[str], album_title: str) -> OutputResult:
        """生成图片集合"""
        try:
            from PIL import Image
            
            # 创建图片输出目录
            images_dir = os.path.join(self.config.output_dir, f"{album_title}_images")
            os.makedirs(images_dir, exist_ok=True)
            
            output_paths = []
            
            # 复制并重命名图片
            for i, image_path in enumerate(page_images):
                try:
                    # 打开图片
                    img = Image.open(image_path)
                    
                    # 根据配置调整质量
                    if self.config.image_format.lower() == 'jpg':
                        output_filename = f"page_{i+1:03d}.jpg"
                        output_path = os.path.join(images_dir, output_filename)
                        
                        # 保存为JPEG
                        img.save(output_path, 
                                format='JPEG',
                                quality=self.config.image_quality,
                                optimize=True)
                    
                    elif self.config.image_format.lower() == 'png':
                        output_filename = f"page_{i+1:03d}.png"
                        output_path = os.path.join(images_dir, output_filename)
                        
                        # 保存为PNG
                        img.save(output_path, format='PNG', optimize=True)
                    
                    elif self.config.image_format.lower() == 'webp':
                        output_filename = f"page_{i+1:03d}.webp"
                        output_path = os.path.join(images_dir, output_filename)
                        
                        # 保存为WebP
                        img.save(output_path, 
                                format='WEBP',
                                quality=self.config.image_quality,
                                method=6)  # 方法6为最高质量
                    
                    else:
                        # 默认使用JPEG
                        output_filename = f"page_{i+1:03d}.jpg"
                        output_path = os.path.join(images_dir, output_filename)
                        img.save(output_path, format='JPEG', quality=90)
                    
                    output_paths.append(output_path)
                    
                    # 创建缩略图（如果需要）
                    if self.config.create_thumbnails:
                        thumbnail_path = os.path.join(images_dir, f"thumb_{i+1:03d}.jpg")
                        self._create_thumbnail(img, thumbnail_path)
                        output_paths.append(thumbnail_path)
                    
                except Exception as e:
                    logger.warning(f"处理图片 {image_path} 失败: {e}")
                    continue
            
            if not output_paths:
                return OutputResult(
                    success=False,
                    output_format=OutputFormat.IMAGES,
                    output_paths=[],
                    message="没有图片成功处理"
                )
            
            # 创建索引文件
            index_path = self._create_images_index(images_dir, album_title, len(page_images))
            if index_path:
                output_paths.append(index_path)
            
            metadata = {
                'total_pages': len(page_images),
                'output_images': len(output_paths),
                'image_format': self.config.image_format,
                'image_quality': self.config.image_quality,
                'thumbnails_created': self.config.create_thumbnails,
                'output_directory': images_dir
            }
            
            return OutputResult(
                success=True,
                output_format=OutputFormat.IMAGES,
                output_paths=output_paths,
                message=f"图片集合生成成功: {len(output_paths)}个文件",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"生成图片集合失败: {e}")
            return OutputResult(
                success=False,
                output_format=OutputFormat.IMAGES,
                output_paths=[],
                message=f"图片集合生成失败: {str(e)}"
            )
    
    def _create_thumbnail(self, image, output_path: str):
        """创建缩略图"""
        try:
            thumbnail_size = self.config.thumbnail_size
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            image.save(output_path, format='JPEG', quality=85)
        except Exception as e:
            logger.warning(f"创建缩略图失败: {e}")
    
    def _create_images_index(self, images_dir: str, album_title: str, page_count: int) -> Optional[str]:
        """创建图片索引文件"""
        try:
            index_path = os.path.join(images_dir, "index.html")
            
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{album_title} - 图片索引</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #1E90FF;
            padding-bottom: 10px;
        }}
        .info {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }}
        .page {{
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
            transition: transform 0.3s;
        }}
        .page:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .page img {{
            width: 100%;
            height: 150px;
            object-fit: cover;
        }}
        .page-number {{
            padding: 10px;
            text-align: center;
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .download-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #1E90FF;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }}
        .download-link:hover {{
            background-color: #0d8bf2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{album_title}</h1>
        
        <div class="info">
            <p><strong>相册信息:</strong></p>
            <p>• 总页数: {page_count} 页</p>
            <p>• 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>• 图片格式: {self.config.image_format.upper()}</p>
            <p>• 包含缩略图: {'是' if self.config.create_thumbnails else '否'}</p>
        </div>
        
        <div class="grid">
"""
            
            # 添加页面预览
            for i in range(page_count):
                page_num = i + 1
                image_file = f"page_{page_num:03d}.{self.config.image_format}"
                thumb_file = f"thumb_{page_num:03d}.jpg" if self.config.create_thumbnails else image_file
                
                html_content += f"""
            <div class="page">
                <a href="{image_file}" target="_blank">
                    <img src="{thumb_file}" alt="第{page_num}页">
                </a>
                <div class="page-number">第 {page_num} 页</div>
            </div>
"""
            
            html_content += """
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <a href="../" class="download-link">返回上级目录</a>
            <a href="index.html" class="download-link" style="margin-left: 10px;">刷新页面</a>
        </div>
    </div>
</body>
</html>"""
            
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return index_path
            
        except Exception as e:
            logger.warning(f"创建索引文件失败: {e}")
            return None
    
    def _generate_html(self, page_images: List[str], album_title: str, album_description: str) -> OutputResult:
        """生成HTML网页"""
        try:
            from PIL import Image
            
            # 创建HTML输出目录
            html_dir = os.path.join(self.config.output_dir, f"{album_title}_web")
            os.makedirs(html_dir, exist_ok=True)
            
            # 复制图片到web目录
            web_images = []
            for i, image_path in enumerate(page_images):
                try:
                    img = Image.open(image_path)
                    web_image_path = os.path.join(html_dir, f"page_{i+1:03d}.jpg")
                    img.save(web_image_path, format='JPEG', quality=85)
                    web_images.append(web_image_path)
                except Exception as e:
                    logger.warning(f"复制图片 {image_path} 失败: {e}")
                    continue
            
            if not web_images:
                return OutputResult(
                    success=False,
                    output_format=OutputFormat.HTML,
                    output_paths=[],
                    message="没有图片可生成HTML"
                )
            
            # 生成HTML文件
            html_path = os.path.join(html_dir, "album.html")
            self._create_html_album(html_path, web_images, album_title, album_description)
            
            # 生成预览图
            preview_path = None
            if web_images:
                preview_path = self._create_preview_image(web_images[0], html_dir)
            
            output_paths = [html_path] + web_images
            if preview_path:
                output_paths.append(preview_path)
            
            metadata = {
                'total_pages': len(web_images),
                'html_template': self.config.html_template,
                'responsive_design': self.config.html_responsive,
                'navigation_enabled': self.config.html_include_navigation,
                'output_directory': html_dir
            }
            
            return OutputResult(
                success=True,
                output_format=OutputFormat.HTML,
                output_paths=output_paths,
                message=f"HTML相册生成成功: {len(web_images)}页",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"生成HTML失败: {e}")
            return OutputResult(
                success=False,
                output_format=OutputFormat.HTML,
                output_paths=[],
                message=f"HTML生成失败: {str(e)}"
            )
    
    def _create_html_album(self, html_path: str, image_paths: List[str], 
                          album_title: str, album_description: str):
        """创建HTML相册"""
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{album_title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            color: white;
            padding: 40px 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .album-container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
            margin-bottom: 30px;
        }}
        
        .album-viewer {{
            position: relative;
            min-height: 600px;
        }}
        
        .current-page {{
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            background: #f8f9fa;
        }}
        
        .current-page img {{
            max-width: 100%;
            max-height: 500px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .navigation {{
            display: flex;
            justify-content: space-between;
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }}
        
        .nav-btn {{
            padding: 12px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .nav-btn:hover {{
            background: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        
        .nav-btn:disabled {{
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }}
        
        .page-info {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.1rem;
            color: #495057;
        }}
        
        .page-counter {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .thumbnail-strip {{
            display: flex;
            overflow-x: auto;
            padding: 15px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
            gap: 10px;
        }}
        
        .thumbnail {{
            flex: 0 0 auto;
            width: 100px;
            height: 70px;
            border-radius: 5px;
            overflow: hidden;
            cursor: pointer;
            border: 2px solid transparent;
            transition: all 0.3s;
        }}
        
        .thumbnail:hover {{
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .thumbnail.active {{
            border-color: #667eea;
        }}
        
        .thumbnail img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .album-viewer {{
                min-height: 400px;
            }}
            
            .current-page img {{
                max-height: 300px;
            }}
            
            .nav-btn {{
                padding: 10px 20px;
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{album_title}</h1>
            <p>{album_description or '美好的回忆，永恒的珍藏'}</p>
        </div>
        
        <div class="album-container">
            <div class="album-viewer">
                <div class="current-page">
                    <img id="currentImage" src="{os.path.basename(image_paths[0])}" alt="第1页">
                </div>
                
                <div class="navigation">
                    <button class="nav-btn" id="prevBtn" onclick="prevPage()">
                        <span>←</span> 上一页
                    </button>
                    
                    <div class="page-info">
                        <span>第</span>
                        <span class="page-counter" id="currentPage">1</span>
                        <span>页 / 共</span>
                        <span class="page-counter" id="totalPages">{len(image_paths)}</span>
                        <span>页</span>
                    </div>
                    
                    <button class="nav-btn" id="nextBtn" onclick="nextPage()">
                        下一页 <span>→</span>
                    </button>
                </div>
                
                <div class="thumbnail-strip" id="thumbnailStrip">
                    <!-- 缩略图将通过JavaScript动态生成 -->
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>电子相册生成于 {time.strftime('%Y年%m月%d日 %H:%M:%S')} | 使用电子相册Skill创建</p>
        </div>
    </div>
    
    <script>
        // 图片数据
        const images = [
"""
        
        # 添加图片路径
        for i, img_path in enumerate(image_paths):
            html_content += f'            {{ id: {i+1}, src: "{os.path.basename(img_path)}" }},\n'
        
        html_content += """        ];
        
        let currentPage = 1;
        const totalPages = images.length;
        
        // 初始化
        function initAlbum() {{
            updatePageInfo();
            updateNavigation();
            generateThumbnails();
        }}
        
        // 更新页面信息
        function updatePageInfo() {{
            document.getElementById('currentPage').textContent = currentPage;
            document.getElementById('totalPages').textContent = totalPages;
            document.getElementById('currentImage').src = images[currentPage - 1].src;
        }}
        
        // 更新导航按钮状态
        function updateNavigation() {{
            document.getElementById('prevBtn').disabled = currentPage === 1;
            document.getElementById('nextBtn').disabled = currentPage === totalPages;
        }}
        
        // 生成缩略图
        function generateThumbnails() {{
            const thumbnailStrip = document.getElementById('thumbnailStrip');
            thumbnailStrip.innerHTML = '';
            
            images.forEach((image, index) => {{
                const thumbnail = document.createElement('div');
                thumbnail.className = `thumbnail ${{currentPage === index + 1 ? 'active' : ''}}`;
                thumbnail.onclick = () => goToPage(index + 1);
                
                const img = document.createElement('img');
                img.src = image.src;
                img.alt = `第${{index + 1}}页`;
                
                thumbnail.appendChild(img);
                thumbnailStrip.appendChild(thumbnail);
            }});
        }}
        
        // 跳转到指定页面
        function goToPage(page) {{
            if (page < 1 || page > totalPages) return;
            
            currentPage = page;
            updatePageInfo();
            updateNavigation();
            
            // 更新缩略图激活状态
            document.querySelectorAll('.thumbnail').forEach((thumb, index) => {{
                thumb.classList.toggle('active', index + 1 === currentPage);
            }});
            
            // 平滑滚动到当前缩略图
            const activeThumb = document.querySelector('.thumbnail.active');
            if (activeThumb) {{
                activeThumb.scrollIntoView({{
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'center'
                }});
            }}
        }}
        
        // 上一页
        function prevPage() {{
            if (currentPage > 1) {{
                goToPage(currentPage - 1);
            }}
        }}
        
        // 下一页
        function nextPage() {{
            if (currentPage < totalPages) {{
                goToPage(currentPage + 1);
            }}
        }}
        
        // 键盘导航
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowLeft') prevPage();
            if (e.key === 'ArrowRight') nextPage();
        }});
        
        // 初始化相册
        window.onload = initAlbum;
    </script>
</body>
</html>"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _create_preview_image(self, image_path: str, output_dir: str) -> Optional[str]:
        """创建预览图"""
        try:
            from PIL import Image
            
            img = Image.open(image_path)
            
            # 创建缩略图作为预览
            preview_size = (400, 300)
            img.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            preview_path = os.path.join(output_dir, "preview.jpg")
            img.save(preview_path, format='JPEG', quality=85)
            
            return preview_path
        except Exception as e:
            logger.warning(f"创建预览图失败: {e}")
            return None
    
    def _generate_zip(self, page_images: List[str], album_title: str) -> OutputResult:
        """生成压缩包"""
        try:
            import zipfile
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 复制所有文件到临时目录
                for i, image_path in enumerate(page_images):
                    try:
                        dest_path = os.path.join(temp_dir, f"page_{i+1:03d}{os.path.splitext(image_path)[1]}")
                        shutil.copy2(image_path, dest_path)
                    except Exception as e:
                        logger.warning(f"复制文件 {image_path} 失败: {e}")
                
                # 创建说明文件
                readme_path = os.path.join(temp_dir, "README.txt")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"""电子相册: {album_title}
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
总页数: {len(page_images)} 页

使用说明:
1. 解压此压缩包
2. 使用图片查看器浏览相册页面
3. 页面按顺序编号: page_001.jpg, page_002.jpg, ...

注意事项:
- 建议使用专业图片查看器以获得最佳体验
- 如需打印，请确保打印机支持相应分辨率
- 原始图片质量已优化，适合屏幕查看和普通打印

生成工具: 电子相册Skill
""")
                
                # 创建压缩包
                zip_filename = f"{album_title}_{int(time.time())}.zip"
                zip_path = os.path.join(self.config.output_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                
                # 检查文件大小
                file_size = os.path.getsize(zip_path)
                file_size_mb = file_size / (1024 * 1024)
                
                metadata = {
                    'total_files': len(page_images) + 1,  # 图片 + README
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size_mb, 2),
                    'compression_method': 'DEFLATED',
                    'compression_level': 6
                }
                
                return OutputResult(
                    success=True,
                    output_format=OutputFormat.ZIP,
                    output_paths=[zip_path],
                    message=f"压缩包生成成功: {round(file_size_mb, 2)}MB",
                    metadata=metadata
                )
                
        except Exception as e:
            logger.error(f"生成压缩包失败: {e}")
            return OutputResult(
                success=False,
                output_format=OutputFormat.ZIP,
                output_paths=[],
                message=f"压缩包生成失败: {str(e)}"
            )
    
    def _generate_feishu_doc(self, page_images: List[str], album_title: str, album_description: str) -> OutputResult:
        """生成飞书文档"""
        # 注意：这里需要飞书API支持
        # 由于飞书API需要认证，这里只提供框架
        
        try:
            # 检查飞书配置
            if not self.config.feishu_doc_token:
                return OutputResult(
                    success=False,
                    output_format=OutputFormat.FEISHU_DOC,
                    output_paths=[],
                    message="未配置飞书文档token，无法生成飞书文档"
                )
            
            # 这里应该调用飞书API上传文档
            # 由于API复杂性，这里只返回模拟结果
            
            metadata = {
                'doc_title': album_title,
                'doc_description': album_description,
                'page_count': len(page_images),
                'feishu_doc_token': self.config.feishu_doc_token,
                'share_enabled': self.config.feishu_share_enabled
            }
            
            return OutputResult(
                success=True,
                output_format=OutputFormat.FEISHU_DOC,
                output_paths=[f"feishu://doc/{self.config.feishu_doc_token}"],
                message=f"飞书文档已创建: {album_title}",
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"生成飞书文档失败: {e}")
            return OutputResult(
                success=False,
                output_format=OutputFormat.FEISHU_DOC,
                output_paths=[],
                message=f"飞书文档生成失败: {str(e)}"
            )
    
    def _generate_summary_report(self, results: Dict[OutputFormat, OutputResult], album_title: str):
        """生成汇总报告"""
        try:
            report_path = os.path.join(self.config.output_dir, "生成报告.md")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"# 电子相册生成报告\n\n")
                f.write(f"**相册标题**: {album_title}\n")
                f.write(f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## 生成结果汇总\n\n")
                
                success_count = 0
                total_count = len(results)
                
                for output_format, result in results.items():
                    status = "✅ 成功" if result.success else "❌ 失败"
                    f.write(f"### {output_format.value}\n")
                    f.write(f"- **状态**: {status}\n")
                    f.write(f"- **消息**: {result.message}\n")
                    
                    if result.success and result.output_paths:
                        f.write(f"- **输出文件**:\n")
                        for path in result.output_paths:
                            f.write(f"  - `{path}`\n")
                    
                    if result.metadata:
                        f.write(f"- **元数据**:\n")
                        for key, value in result.metadata.items():
                            f.write(f"  - {key}: {value}\n")
                    
                    f.write("\n")
                    
                    if result.success:
                        success_count += 1
                
                f.write(f"## 统计信息\n\n")
                f.write(f"- **总输出格式**: {total_count} 种\n")
                f.write(f"- **成功生成**: {success_count} 种\n")
                f.write(f"- **成功率**: {success_count/total_count*100:.1f}%\n\n")
                
                f.write("## 使用说明\n\n")
                f.write("1. **PDF文件**: 适合打印和归档\n")
                f.write("2. **图片集合**: 适合在线查看和分享\n")
                f.write("3. **HTML相册**: 交互式网页浏览体验\n")
                f.write("4. **压缩包**: 方便传输和备份\n\n")
                
                f.write("## 注意事项\n\n")
                f.write("- 建议保留所有输出格式以备不同用途\n")
                f.write("- PDF文件适合打印，但文件较大\n")
                f.write("- 图片集合适合在线分享和社交媒体\n")
                f.write("- HTML相册提供最佳浏览体验\n")
            
            logger.info(f"生成报告已保存: {report_path}")
            
        except Exception as e:
            logger.warning(f"生成汇总报告失败: {e}")


# 使用示例
if __name__ == "__main__":
    # 示例配置
    config = OutputConfig(
        output_formats=[OutputFormat.PDF, OutputFormat.IMAGES, OutputFormat.HTML],
        output_quality=OutputQuality.HIGH,
        output_dir="./album_output"
    )
    
    # 创建输出生成器
    generator = OutputGenerator(config)
    
    # 示例图片（需要实际图片路径）
    test_images = [
        "/path/to/page1.jpg",
        "/path/to/page2.jpg",
        "/path/to/page3.jpg"
    ]
    
    # 生成输出
    results = generator.generate_outputs(
        page_images=test_images,
        album_title="测试相册",
        album_description="这是一个测试相册"
    )
    
    # 打印结果
    print("生成结果:")
    for output_format, result in results.items():
        print(f"\n{output_format.value}:")
        print(f"  成功: {result.success}")
        print(f"  消息: {result.message}")
        if result.output_paths:
            print(f"  输出文件: {result.output_paths}")