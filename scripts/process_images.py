#!/usr/bin/env python3
"""
图片处理模块
负责图片的批量处理、优化和格式转换
基于原始项目中的process_images.py优化
"""

import os
import sys
import logging
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# 图像处理库
try:
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillow库未安装，图片处理功能将受限")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """图片格式枚举"""
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"
    BMP = "BMP"
    GIF = "GIF"


class ResizeStrategy(Enum):
    """缩放策略枚举"""
    FIT = "fit"        # 适应目标尺寸，保持比例
    CROP = "crop"      # 裁剪到目标尺寸
    PAD = "pad"        # 填充到目标尺寸
    STRETCH = "stretch" # 拉伸到目标尺寸


@dataclass
class ImageProcessingConfig:
    """图片处理配置"""
    # 尺寸配置
    target_size: Tuple[int, int] = (1200, 800)  # 目标尺寸 (宽, 高)
    resize_strategy: ResizeStrategy = ResizeStrategy.FIT
    
    # 质量配置
    quality: int = 85  # 质量 (1-100)
    optimize: bool = True
    
    # 增强配置
    auto_orient: bool = True  # 自动方向校正
    enhance_colors: bool = True  # 色彩增强
    enhance_sharpness: bool = False  # 锐化增强
    enhance_brightness: float = 1.0  # 亮度增强 (1.0为原图)
    enhance_contrast: float = 1.0  # 对比度增强 (1.0为原图)
    
    # 格式配置
    output_format: ImageFormat = ImageFormat.JPEG
    convert_to_rgb: bool = True  # 转换为RGB模式
    
    # 水印配置
    watermark_text: Optional[str] = None
    watermark_position: str = "bottom-right"  # top-left, top-right, bottom-left, bottom-right, center
    
    # 其他配置
    preserve_metadata: bool = True  # 保留元数据
    create_thumbnails: bool = False  # 创建缩略图
    thumbnail_size: Tuple[int, int] = (300, 200)  # 缩略图尺寸
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['target_size'] = list(data['target_size'])
        data['thumbnail_size'] = list(data['thumbnail_size'])
        data['resize_strategy'] = data['resize_strategy'].value
        data['output_format'] = data['output_format'].value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageProcessingConfig':
        """从字典创建"""
        if 'target_size' in data and isinstance(data['target_size'], list):
            data['target_size'] = tuple(data['target_size'])
        if 'thumbnail_size' in data and isinstance(data['thumbnail_size'], list):
            data['thumbnail_size'] = tuple(data['thumbnail_size'])
        if 'resize_strategy' in data:
            data['resize_strategy'] = ResizeStrategy(data['resize_strategy'])
        if 'output_format' in data:
            data['output_format'] = ImageFormat(data['output_format'])
        return cls(**data)


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self, config: Optional[ImageProcessingConfig] = None):
        """
        初始化图片处理器
        
        Args:
            config: 处理配置，如果为None则使用默认配置
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow库未安装，请先安装: pip install Pillow")
        
        self.config = config or ImageProcessingConfig()
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']
        
        logger.info("图片处理器初始化完成")
        logger.info(f"配置: {self.config.to_dict()}")
    
    def batch_process(self, image_paths: List[str], 
                     output_dir: Optional[str] = None,
                     config: Optional[ImageProcessingConfig] = None) -> List[str]:
        """
        批量处理图片
        
        Args:
            image_paths: 图片路径列表
            output_dir: 输出目录，如果为None则覆盖原文件
            config: 处理配置，如果为None则使用实例配置
            
        Returns:
            处理后的图片路径列表
        """
        if config:
            self.config = config
        
        if not image_paths:
            logger.warning("没有需要处理的图片")
            return []
        
        # 创建输出目录
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        processed_paths = []
        total_count = len(image_paths)
        
        logger.info(f"开始批量处理 {total_count} 张图片")
        
        for i, image_path in enumerate(image_paths, 1):
            try:
                # 处理单张图片
                processed_path = self.process_single_image(
                    image_path, 
                    output_dir,
                    f"({i}/{total_count})"
                )
                
                if processed_path:
                    processed_paths.append(processed_path)
                    logger.info(f"处理完成: {image_path} -> {processed_path}")
                else:
                    logger.warning(f"处理失败: {image_path}")
                    
            except Exception as e:
                logger.error(f"处理图片时出错 {image_path}: {e}")
                # 继续处理其他图片
        
        logger.info(f"批量处理完成，成功处理 {len(processed_paths)}/{total_count} 张图片")
        return processed_paths
    
    def process_single_image(self, image_path: str, 
                           output_dir: Optional[str] = None,
                           progress_prefix: str = "") -> Optional[str]:
        """
        处理单张图片
        
        Args:
            image_path: 图片路径
            output_dir: 输出目录
            progress_prefix: 进度前缀
            
        Returns:
            处理后的图片路径，如果失败则返回None
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logger.error(f"文件不存在: {image_path}")
                return None
            
            # 检查文件格式
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in self.supported_formats:
                logger.warning(f"不支持的格式: {file_ext}, 跳过: {image_path}")
                return None
            
            # 打开图片
            logger.debug(f"{progress_prefix} 打开图片: {image_path}")
            with Image.open(image_path) as img:
                # 保存原始信息
                original_format = img.format
                original_mode = img.mode
                original_size = img.size
                
                # 处理图片
                processed_img = self._process_image_object(img)
                
                # 确定输出路径
                output_path = self._get_output_path(image_path, output_dir)
                
                # 保存图片
                save_kwargs = self._get_save_kwargs()
                processed_img.save(output_path, **save_kwargs)
                
                # 创建缩略图（如果需要）
                if self.config.create_thumbnails:
                    self._create_thumbnail(processed_img, output_path)
                
                logger.debug(f"{progress_prefix} 处理完成: {original_size} -> {processed_img.size}")
                return output_path
                
        except Exception as e:
            logger.error(f"{progress_prefix} 处理图片失败 {image_path}: {e}")
            return None
    
    def _process_image_object(self, img: Image.Image) -> Image.Image:
        """
        处理图片对象
        
        Args:
            img: PIL图片对象
            
        Returns:
            处理后的图片对象
        """
        # 1. 自动方向校正
        if self.config.auto_orient:
            img = self._auto_orient_image(img)
        
        # 2. 转换为RGB模式（如果需要）
        if self.config.convert_to_rgb and img.mode != 'RGB':
            if img.mode == 'RGBA':
                # 透明背景处理
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                img = background
            else:
                img = img.convert('RGB')
        
        # 3. 调整尺寸
        img = self._resize_image(img)
        
        # 4. 色彩增强
        if self.config.enhance_colors:
            img = self._enhance_colors(img)
        
        # 5. 亮度对比度调整
        if self.config.enhance_brightness != 1.0 or self.config.enhance_contrast != 1.0:
            img = self._adjust_brightness_contrast(img)
        
        # 6. 锐化增强
        if self.config.enhance_sharpness:
            img = self._enhance_sharpness(img)
        
        # 7. 添加水印
        if self.config.watermark_text:
            img = self._add_watermark(img)
        
        return img
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """调整图片尺寸"""
        if not self.config.target_size:
            return img
        
        target_width, target_height = self.config.target_size
        
        # 获取原始尺寸
        original_width, original_height = img.size
        
        # 如果图片已经符合目标尺寸，直接返回
        if original_width == target_width and original_height == target_height:
            return img
        
        # 根据策略调整尺寸
        if self.config.resize_strategy == 'fit':
            # 保持宽高比，适应目标尺寸
            ratio = min(target_width / original_width, target_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        elif self.config.resize_strategy == 'fill':
            # 填充目标尺寸，可能会裁剪
            ratio = max(target_width / original_width, target_height / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 居中裁剪
            left = (new_width - target_width) // 2
            top = (new_height - target_height) // 2
            right = left + target_width
            bottom = top + target_height
            img = img.crop((left, top, right, bottom))
        
        elif self.config.resize_strategy == 'stretch':
            # 拉伸到目标尺寸
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        return img
    
    def _enhance_colors(self, img: Image.Image) -> Image.Image:
        """增强图片色彩"""
        from PIL import ImageEnhance
        
        # 调整亮度
        if self.config.enhance_brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.config.enhance_brightness)
        
        # 调整对比度
        if self.config.enhance_contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.config.enhance_contrast)
        
        # 调整锐度
        if self.config.enhance_sharpness:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)  # 适度增强锐度
        
        return img
    
    def _get_output_path(self, input_path: str, output_dir: str) -> str:
        """生成输出文件路径"""
        import os
        from pathlib import Path
        
        # 获取输入文件名（不含扩展名）
        input_file = Path(input_path)
        stem = input_file.stem
        
        # 获取输出格式（可能是字符串或枚举）
        output_format = self.config.output_format
        if hasattr(output_format, 'value'):
            output_format = output_format.value
        elif hasattr(output_format, 'name'):
            output_format = output_format.name
        
        # 转换为小写字符串
        format_str = str(output_format).lower()
        
        # 生成输出文件名
        output_filename = f"{stem}_processed.{format_str}"
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 返回完整输出路径
        return os.path.join(output_dir, output_filename)
    
    def _get_save_kwargs(self) -> dict:
        """获取图片保存参数"""
        kwargs = {}
        
        # 根据输出格式设置参数
        format_str = str(self.config.output_format).upper()
        
        if format_str == 'JPEG' or format_str == 'JPG':
            kwargs['quality'] = self.config.quality
            kwargs['optimize'] = self.config.optimize
            if self.config.convert_to_rgb:
                kwargs['subsampling'] = 0  # 4:4:4 chroma subsampling for better quality
        elif format_str == 'PNG':
            kwargs['compress_level'] = 9 - int(self.config.quality / 10)  # 0-9, 0=no compression
            kwargs['optimize'] = self.config.optimize
        
        return kwargs
    
    def _auto_orient_image(self, img: Image.Image) -> Image.Image:
        """自动方向校正"""
        try:
            # 获取EXIF方向信息
            exif = img._getexif()
            if exif:
                orientation = exif.get(274)  # 274是方向标签
                
                # 根据方向信息旋转图片
                if orientation == 2:
                    img = ImageOps.mirror(img)
                elif orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 4:
                    img = ImageOps.flip(img)
                elif orientation == 5:
                    img = ImageOps.mirror(img.rotate(-90, expand=True))
                elif orientation == 6:
                    img = img.rotate(-90, expand=True)
                elif orientation == 7:
                    img = ImageOps.mirror(img.rotate(90, expand=True))
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except Exception:
            # 如果EXIF信息读取失败，保持原图不变
            pass
        
        return img