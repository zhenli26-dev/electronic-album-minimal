#!/usr/bin/env python3
"""
模板应用模块
负责将处理后的图片应用到相册模板中
"""

import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import shutil

# 图像处理库
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillow库未安装，模板应用功能将受限")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """模板类型枚举"""
    COVER = "cover"           # 封面模板
    DIRECTORY = "directory"   # 目录模板
    SINGLE = "single"         # 单张图片模板
    TWO_IMAGES = "two"        # 两张图片模板
    THREE_IMAGES = "three"    # 三张图片模板
    FOUR_IMAGES = "four"      # 四张图片模板


class LayoutStyle(Enum):
    """布局风格枚举"""
    SIMPLE = "simple"         # 简约风格
    ELEGANT = "elegant"       # 优雅风格
    MODERN = "modern"         # 现代风格
    PLAYFUL = "playful"       # 活泼风格
    BUSINESS = "business"     # 商务风格


@dataclass
class TemplateConfig:
    """模板配置"""
    template_type: TemplateType = TemplateType.SINGLE
    layout_style: LayoutStyle = LayoutStyle.ELEGANT
    
    # 尺寸配置
    page_width: int = 1200
    page_height: int = 800
    margin: int = 50
    spacing: int = 20
    
    # 颜色配置
    background_color: str = "#FFFFFF"
    text_color: str = "#333333"
    accent_color: str = "#1E90FF"
    
    # 字体配置
    font_size_title: int = 36
    font_size_subtitle: int = 24
    font_size_body: int = 16
    font_size_caption: int = 14
    
    # 图片配置
    image_border: bool = True
    border_color: str = "#E0E0E0"
    border_width: int = 2
    image_corner_radius: int = 10
    shadow_enabled: bool = True
    
    # 文字配置
    caption_enabled: bool = True
    max_caption_length: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['template_type'] = data['template_type'].value
        data['layout_style'] = data['layout_style'].value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateConfig':
        """从字典创建"""
        if 'template_type' in data:
            data['template_type'] = TemplateType(data['template_type'])
        if 'layout_style' in data:
            data['layout_style'] = LayoutStyle(data['layout_style'])
        return cls(**data)


@dataclass
class AlbumPage:
    """相册页面"""
    page_number: int
    template_type: TemplateType
    images: List[str]  # 图片路径列表
    captions: List[str]  # 图片说明列表
    title: Optional[str] = None
    subtitle: Optional[str] = None
    background_color: str = "#FFFFFF"
    output_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'page_number': self.page_number,
            'template_type': self.template_type.value,
            'images': self.images,
            'captions': self.captions,
            'title': self.title,
            'subtitle': self.subtitle,
            'background_color': self.background_color,
            'output_path': self.output_path
        }


class TemplateEngine:
    """模板引擎"""
    
    def __init__(self, templates_dir: str, config: Optional[TemplateConfig] = None):
        """
        初始化模板引擎
        
        Args:
            templates_dir: 模板目录路径
            config: 模板配置
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow库未安装，请先安装: pip install Pillow")
        
        self.templates_dir = templates_dir
        self.config = config or TemplateConfig()
        
        # 加载模板文件
        self.templates = self._load_templates()
        
        # 尝试加载字体
        self.fonts = self._load_fonts()
        
        logger.info("模板引擎初始化完成")
        logger.info(f"模板目录: {templates_dir}")
        logger.info(f"可用模板: {list(self.templates.keys())}")
    
    def _load_templates(self) -> Dict[str, str]:
        """加载模板文件"""
        templates = {}
        template_files = [
            ("01_cover.jpg", TemplateType.COVER),
            ("02_directory.jpg", TemplateType.DIRECTORY),
            ("03_single_image.jpg", TemplateType.SINGLE),
            ("04_two_images.jpg", TemplateType.TWO_IMAGES),
            ("05_three_images.jpg", TemplateType.THREE_IMAGES),
            ("06_four_images.md", TemplateType.FOUR_IMAGES)
        ]
        
        for filename, template_type in template_files:
            template_path = os.path.join(self.templates_dir, filename)
            if os.path.exists(template_path):
                templates[template_type.value] = template_path
                logger.debug(f"加载模板: {template_type.value} -> {template_path}")
            else:
                logger.warning(f"模板文件不存在: {template_path}")
        
        return templates
    
    def _load_fonts(self) -> Dict[str, Optional[ImageFont.FreeTypeFont]]:
        """加载字体"""
        fonts = {}
        
        # 尝试加载中文字体
        font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "C:/Windows/Fonts/msyh.ttc"
        ]
        
        # 默认字体（如果找不到中文字体）
        default_font = None
        try:
            default_font = ImageFont.load_default()
        except:
            pass
        
        # 标题字体
        try:
            for path in font_paths:
                if os.path.exists(path):
                    fonts['title'] = ImageFont.truetype(path, self.config.font_size_title)
                    fonts['subtitle'] = ImageFont.truetype(path, self.config.font_size_subtitle)
                    fonts['body'] = ImageFont.truetype(path, self.config.font_size_body)
                    fonts['caption'] = ImageFont.truetype(path, self.config.font_size_caption)
                    logger.info(f"加载字体: {path}")
                    break
        except Exception as e:
            logger.warning(f"加载字体失败: {e}, 使用默认字体")
            fonts['title'] = default_font
            fonts['subtitle'] = default_font
            fonts['body'] = default_font
            fonts['caption'] = default_font
        
        return fonts
    
    def apply_template(self, album_page: AlbumPage, output_dir: str) -> str:
        """
        应用模板生成页面
        
        Args:
            album_page: 相册页面数据
            output_dir: 输出目录
            
        Returns:
            生成的页面图片路径
        """
        try:
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 根据模板类型选择生成方法
            template_type = album_page.template_type
            
            if template_type == TemplateType.COVER:
                output_path = self._create_cover_page(album_page, output_dir)
            elif template_type == TemplateType.DIRECTORY:
                output_path = self._create_directory_page(album_page, output_dir)
            elif template_type == TemplateType.SINGLE:
                output_path = self._create_single_image_page(album_page, output_dir)
            elif template_type == TemplateType.TWO_IMAGES:
                output_path = self._create_two_images_page(album_page, output_dir)
            elif template_type == TemplateType.THREE_IMAGES:
                output_path = self._create_three_images_page(album_page, output_dir)
            elif template_type == TemplateType.FOUR_IMAGES:
                output_path = self._create_four_images_page(album_page, output_dir)
            else:
                raise ValueError(f"不支持的模板类型: {template_type}")
            
            # 更新页面输出路径
            album_page.output_path = output_path
            
            logger.info(f"页面生成完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"应用模板失败: {e}")
            raise
    
    def _create_cover_page(self, album_page: AlbumPage, output_dir: str) -> str:
        """创建封面页面"""
        # 创建空白画布
        page = Image.new('RGB', 
                        (self.config.page_width, self.config.page_height),
                        album_page.background_color)
        draw = ImageDraw.Draw(page)
        
        # 如果有图片，添加主图
        if album_page.images and len(album_page.images) > 0:
            try:
                main_image = Image.open(album_page.images[0])
                main_image = self._process_image_for_template(main_image)
                
                # 计算图片位置（居中）
                img_x = (self.config.page_width - main_image.width) // 2
                img_y = (self.config.page_height - main_image.height) // 3
                
                # 添加阴影效果
                if self.config.shadow_enabled:
                    shadow = self._create_shadow(main_image)
                    page.paste(shadow, (img_x + 5, img_y + 5), shadow)
                
                page.paste(main_image, (img_x, img_y))
                
            except Exception as e:
                logger.warning(f"添加封面图片失败: {e}")
        
        # 添加标题
        if album_page.title:
            title_font = self.fonts.get('title')
            if title_font:
                # 计算标题位置
                title_bbox = draw.textbbox((0, 0), album_page.title, font=title_font)
                title_width = title_bbox[2] - title_bbox[0]
                title_x = (self.config.page_width - title_width) // 2
                title_y = self.config.page_height * 2 // 3
                
                # 绘制标题
                draw.text((title_x, title_y), album_page.title, 
                         font=title_font, fill=self.config.text_color)
        
        # 添加副标题
        if album_page.subtitle:
            subtitle_font = self.fonts.get('subtitle')
            if subtitle_font:
                subtitle_bbox = draw.textbbox((0, 0), album_page.subtitle, font=subtitle_font)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                subtitle_x = (self.config.page_width - subtitle_width) // 2
                subtitle_y = self.config.page_height * 2 // 3 + 50
                
                draw.text((subtitle_x, subtitle_y), album_page.subtitle,
                         font=subtitle_font, fill=self.config.accent_color)
        
        # 保存页面
        output_path = os.path.join(output_dir, f"page_{album_page.page_number:03d}_cover.jpg")
        page.save(output_path, quality=95)
        
        return output_path
    
    def _create_directory_page(self, album_page: AlbumPage, output_dir: str) -> str:
        """创建目录页面"""
        page = Image.new('RGB',
                        (self.config.page_width, self.config.page_height),
                        album_page.background_color)
        draw = ImageDraw.Draw(page)
        
        # 添加目录标题
        if album_page.title:
            title_font = self.fonts.get('title')
            if title_font:
                title_bbox = draw.textbbox((0, 0), album_page.title, font=title_font)
                title_width = title_bbox[2] - title_bbox[0]
                title_x = (self.config.page_width - title_width) // 2
                title_y = self.config.margin
                
                draw.text((title_x, title_y), album_page.title,
                         font=title_font, fill=self.config.text_color)
        
        # 添加目录项
        if album_page.captions:
            item_font = self.fonts.get('body')
            if item_font:
                start_y = self.config.margin + 100
                line_height = 40
                
                for i, caption in enumerate(album_page.captions):
                    if i >= 10:  # 最多显示10个目录项
                        break
                    
                    item_y = start_y + i * line_height
                    
                    # 页码
                    page_num = f"{i+1:02d}"
                    draw.text((self.config.margin + 50, item_y), page_num,
                             font=item_font, fill=self.config.accent_color)
                    
                    # 目录项
                    draw.text((self.config.margin + 100, item_y), caption,
                             font=item_font, fill=self.config.text_color)
        
        # 保存页面
        output_path = os.path.join(output_dir, f"page_{album_page.page_number:03d}_directory.jpg")
        page.save(output_path, quality=95)
        
        return output_path
    
    def _create_single_image_page(self, album_page: AlbumPage, output_dir: str) -> str:
        """创建单张图片页面"""
        page = Image.new('RGB',
                        (self.config.page_width, self.config.page_height),
                        album_page.background_color)
        draw = ImageDraw.Draw(page)
        
        # 添加图片
        if album_page.images and len(album_page.images) > 0:
            try:
                image = Image.open(album_page.images[0])
                image = self._process_image_for_template(image)
                
                # 计算图片位置（居中）
                img_x = (self.config.page_width - image.width) // 2
                img_y = (self.config.page_height - image.height) // 2 - 50
                
                # 添加阴影
                if self.config.shadow_enabled:
                    shadow = self._create_shadow(image)
                    page.paste(shadow, (img_x + 5, img_y + 5), shadow)
                
                # 添加边框
                if self.config.image_border:
                    border_img = self._add_border(image)
                    page.paste(border_img, (img_x, img_y))
                else:
                    page.paste(image, (img_x, img_y))
                
                # 添加图片说明
                if album_page.captions and len(album_page.captions) > 0:
                    caption = album_page.captions[0]
                    if len(caption) > self.config.max_caption_length:
                        caption = caption[:self.config.max_caption_length] + "..."
                    
                    caption_font = self.fonts.get('caption')
                    if caption_font:
                        caption_bbox = draw.textbbox((0, 0), caption, font=caption_font)
                        caption_width = caption_bbox[2] - caption_bbox[0]
                        caption_x = (self.config.page_width - caption_width) // 2
                        caption_y = img_y + image.height + 20
                        
                        draw.text((caption_x, caption_y), caption,
                                 font=caption_font, fill=self.config.text_color)
                
            except Exception as e:
                logger.warning(f"添加单张图片失败: {e}")
        
        # 保存页面
        output_path = os.path.join(output_dir, f"page_{album_page.page_number:03d}_single.jpg")
        page.save(output_path, quality=95)
        
        return output_path
    
    def _create_two_images_page(self, album_page: AlbumPage, output_dir: str) -> str:
        """创建两张图片页面"""
        page = Image.new('RGB',
                        (self.config.page_width, self.config.page_height),
                        album_page.background_color)
        draw = ImageDraw.Draw(page)
        
        # 计算布局
        available_width = self.config.page_width - 2 * self.config.margin
        available_height = self.config.page_height - 2 * self.config.margin
        
        # 每张图片的宽度（考虑间距）
        image_width = (available_width - self.config.spacing) // 2
        image_height = available_height - 100  # 为说明文字留空间
        
        # 处理并添加图片
        for i in range(min(2, len(album_page.images))):
            try:
                image = Image.open(album_page.images[i])
                image = self._process_image_for_template(image, (image_width, image_height))
                
                # 计算位置
                img_x = self.config.margin + i * (image_width + self.config.spacing)
                img_y = self.config.margin
                
                # 添加阴影
                if self.config.shadow_enabled:
                    shadow = self._create_shadow(image)
                    page.paste(shadow, (img_x + 5, img_y + 5), shadow)
                
                # 添加边框
                if self.config.image_border:
                    border_img = self._add_border(image)
                    page.paste(border_img, (img_x, img_y))
                else:
                    page.paste(image, (img_x, img_y))
                
                # 添加图片说明
                if album_page.captions and i < len(album_page.captions):
                    caption = album_page.captions[i]
                    if len(caption) > self.config.max_caption_length:
                        caption = caption[:self.config.max_caption_length-3] + "..."
                    
                    # 创建说明文本
                    caption_img = self._create_caption_image(caption, image_width)
                    page.paste(caption_img, (img_x, img_y + image_height + 10))
            except Exception as e:
                logger.warning(f"处理第{i+1}张图片失败: {e}")
                continue
        
        return page
    
    def _create_caption_image(self, caption: str, width: int) -> Image.Image:
        """创建图片说明图像"""
        # 创建临时图像用于测量文本
        temp_img = Image.new('RGB', (1, 1), color=self.config.background_color)
        draw = ImageDraw.Draw(temp_img)
        
        # 测量文本尺寸
        bbox = draw.textbbox((0, 0), caption, font=self.config.caption_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 创建说明图像
        caption_height = text_height + 20
        caption_img = Image.new('RGB', (width, caption_height), color=self.config.background_color)
        draw = ImageDraw.Draw(caption_img)
        
        # 绘制文本
        text_x = (width - text_width) // 2
        text_y = 10
        draw.text((text_x, text_y), caption, font=self.config.caption_font, fill=self.config.caption_color)
        
        return caption_img