#!/usr/bin/env python3
"""
电子相册主工作流脚本
负责协调各个模块，完成从需求收集到相册生成的完整流程
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

# 导入各个模块
try:
    from .collect_requirements import RequirementCollector
    from .process_images import ImageProcessor, ImageProcessingConfig
    from .apply_templates import TemplateEngine
    from .generate_output import OutputGenerator
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from collect_requirements import RequirementCollector
    from process_images import ImageProcessor, ImageProcessingConfig
    from apply_templates import TemplateEngine
    from generate_output import OutputGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AlbumConfig:
    """相册配置类"""
    # 基本配置
    title: str = "我的电子相册"
    author: str = "用户"
    theme: str = "default"
    
    # 图片配置
    image_paths: List[str] = None
    image_count: int = 0
    layout_preference: str = "mixed"  # single, two, three, four, mixed
    style: str = "elegant"  # elegant, simple, lively, business
    
    # 文字配置
    need_text: bool = True
    text_amount: str = "moderate"  # minimal, moderate, detailed
    
    # 输出配置
    output_formats: List[str] = None  # feishu, pdf, images
    feishu_doc_token: Optional[str] = None
    
    def __post_init__(self):
        if self.image_paths is None:
            self.image_paths = []
        if self.output_formats is None:
            self.output_formats = ["feishu", "pdf"]
        self.image_count = len(self.image_paths)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlbumConfig':
        """从字典创建"""
        return cls(**data)


class AlbumCreator:
    """相册创建器主类"""
    
    def __init__(self, config: Optional[AlbumConfig] = None, debug: bool = False):
        """
        初始化相册创建器
        
        Args:
            config: 相册配置，如果为None则创建默认配置
            debug: 是否启用调试模式
        """
        self.config = config or AlbumConfig()
        self.debug = debug
        
        # 初始化各个模块
        self.requirement_collector = RequirementCollector()
        self.image_processor = ImageProcessor()
        
        # 获取模板目录路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        templates_dir = os.path.join(script_dir, "..", "templates")
        self.template_engine = TemplateEngine(templates_dir=templates_dir)
        
        self.output_generator = OutputGenerator()
        
        # 处理状态
        self.processed_images = []
        self.generated_pages = []
        self.final_outputs = {}
        
        logger.info("相册创建器初始化完成")
    
    def collect_requirements(self, interactive: bool = True) -> AlbumConfig:
        """
        收集用户需求
        
        Args:
            interactive: 是否使用交互式收集
            
        Returns:
            更新后的配置
        """
        logger.info("开始收集用户需求")
        
        if interactive:
            # 交互式收集需求
            requirements = self.requirement_collector.collect_interactively()
            self.config = AlbumConfig.from_dict(requirements)
        else:
            # 使用现有配置
            logger.info("使用现有配置")
        
        logger.info(f"需求收集完成: {self.config}")
        return self.config
    
    def process_images(self) -> List[str]:
        """
        处理图片
        
        Returns:
            处理后的图片路径列表
        """
        logger.info(f"开始处理 {len(self.config.image_paths)} 张图片")
        
        if not self.config.image_paths:
            logger.warning("没有需要处理的图片")
            return []
        
        try:
            # 批量处理图片
            img_config = ImageProcessingConfig(
                target_size=[1200, 800],
                quality=85,
                auto_orient=True,
                enhance_colors=True
            )
            self.processed_images = self.image_processor.batch_process(
                self.config.image_paths,
                config=img_config
            )
            
            logger.info(f"图片处理完成，共处理 {len(self.processed_images)} 张图片")
            return self.processed_images
            
        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            if self.debug:
                raise
            return []
    
    def apply_templates(self) -> List[str]:
        """
        应用模板生成页面
        
        Returns:
            生成的页面路径列表
        """
        logger.info("开始应用模板生成页面")
        
        if not self.processed_images:
            logger.warning("没有已处理的图片，无法生成页面")
            return []
        
        try:
            # 根据配置选择模板策略
            template_strategy = self._determine_template_strategy()
            
            # 应用模板生成页面
            self.generated_pages = self.template_engine.generate_pages(
                images=self.processed_images,
                strategy=template_strategy,
                config=self.config.to_dict()
            )
            
            logger.info(f"页面生成完成，共生成 {len(self.generated_pages)} 个页面")
            return self.generated_pages
            
        except Exception as e:
            logger.error(f"模板应用失败: {e}")
            if self.debug:
                raise
            return []
    
    def generate_outputs(self) -> Dict[str, Any]:
        """
        生成输出文件
        
        Returns:
            输出文件信息字典
        """
        logger.info("开始生成输出文件")
        
        if not self.generated_pages:
            logger.warning("没有生成的页面，无法生成输出")
            return {}
        
        try:
            self.final_outputs = {}
            
            # 根据配置生成各种格式的输出
            for output_format in self.config.output_formats:
                if output_format == "feishu":
                    if self.config.feishu_doc_token:
                        feishu_output = self.output_generator.generate_feishu_doc(
                            pages=self.generated_pages,
                            doc_token=self.config.feishu_doc_token,
                            title=self.config.title
                        )
                        self.final_outputs["feishu"] = feishu_output
                    else:
                        logger.warning("未提供飞书文档token，跳过飞书文档生成")
                
                elif output_format == "pdf":
                    pdf_output = self.output_generator.generate_pdf(
                        pages=self.generated_pages,
                        output_path=f"{self.config.title}.pdf",
                        title=self.config.title
                    )
                    self.final_outputs["pdf"] = pdf_output
                
                elif output_format == "images":
                    images_output = self.output_generator.export_images(
                        pages=self.generated_pages,
                        output_dir=f"{self.config.title}_pages"
                    )
                    self.final_outputs["images"] = images_output
            
            logger.info(f"输出生成完成: {list(self.final_outputs.keys())}")
            return self.final_outputs
            
        except Exception as e:
            logger.error(f"输出生成失败: {e}")
            if self.debug:
                raise
            return {}
    
    def generate_complete_album(self, interactive: bool = True) -> Dict[str, Any]:
        """
        生成完整相册（完整工作流）
        
        Args:
            interactive: 是否使用交互式需求收集
            
        Returns:
            包含所有输出信息的字典
        """
        logger.info("开始生成完整电子相册")
        
        try:
            # 1. 收集需求
            self.collect_requirements(interactive)
            
            # 2. 处理图片
            self.process_images()
            
            # 3. 应用模板
            self.apply_templates()
            
            # 4. 生成输出
            outputs = self.generate_outputs()
            
            # 5. 返回结果
            result = {
                "status": "success",
                "config": self.config.to_dict(),
                "processed_images_count": len(self.processed_images),
                "generated_pages_count": len(self.generated_pages),
                "outputs": outputs,
                "summary": self._generate_summary()
            }
            
            logger.info("电子相册生成完成")
            return result
            
        except Exception as e:
            logger.error(f"电子相册生成失败: {e}")
            result = {
                "status": "error",
                "error": str(e),
                "config": self.config.to_dict() if self.config else {}
            }
            return result
    
    def _determine_template_strategy(self) -> Dict[str, Any]:
        """
        确定模板应用策略
        
        Returns:
            模板策略配置
        """
        strategy = {
            "cover_template": "01_cover.jpg",
            "directory_template": "02_directory.jpg",
            "content_templates": [],
            "layout_rules": []
        }
        
        # 根据用户偏好确定内容模板
        if self.config.layout_preference == "single":
            strategy["content_templates"] = ["03_single_image.jpg"]
        elif self.config.layout_preference == "two":
            strategy["content_templates"] = ["04_two_images.jpg"]
        elif self.config.layout_preference == "three":
            strategy["content_templates"] = ["05_three_images.jpg"]
        elif self.config.layout_preference == "four":
            strategy["content_templates"] = ["06_four_images.md"]
        else:  # mixed
            # 混合使用多种模板
            strategy["content_templates"] = [
                "03_single_image.jpg",
                "04_two_images.jpg", 
                "05_three_images.jpg"
            ]
            strategy["layout_rules"] = [
                {"template": "03_single_image.jpg", "when": "image_count % 3 == 0"},
                {"template": "04_two_images.jpg", "when": "image_count % 3 == 1"},
                {"template": "05_three_images.jpg", "when": "image_count % 3 == 2"}
            ]
        
        return strategy
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成执行摘要"""
        return {
            "album_title": self.config.title,
            "total_images": len(self.config.image_paths),
            "processed_images": len(self.processed_images),
            "generated_pages": len(self.generated_pages),
            "output_formats": self.config.output_formats,
            "output_files": list(self.final_outputs.keys()),
            "timestamp": datetime.now().isoformat()
        }
    
    def save_config(self, filepath: str = "album_config.json"):
        """保存配置到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"配置已保存到 {filepath}")
    
    def load_config(self, filepath: str = "album_config.json"):
        """从文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        self.config = AlbumConfig.from_dict(config_data)
        logger.info(f"配置已从 {filepath} 加载")


def main():
    """命令行入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(description="电子相册生成工具")
    parser.add_argument("--images", nargs="+", help="图片文件路径列表")
    parser.add_argument("--title", default="我的电子相册", help="相册标题")
    parser.add_argument("--layout", choices=["single", "two", "three", "four", "mixed"], 
                       default="mixed", help="排版偏好")
    parser.add_argument("--style", choices=["elegant", "simple", "lively", "business"],
                       default="elegant", help="风格选择")
    parser.add_argument("--output", nargs="+", choices=["feishu", "pdf", "images"],
                       default=["pdf"], help="输出格式")
    parser.add_argument("--feishu-token", help="飞书文档token")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--interactive", action="store_true", help="交互式模式")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    
    args = parser.parse_args()
    
    # 创建相册创建器
    creator = AlbumCreator(debug=args.debug)
    
    # 如果有配置文件，先加载
    if args.config:
        creator.load_config(args.config)
    
    # 设置命令行参数
    if args.images:
        creator.config.image_paths = args.images
    if args.title:
        creator.config.title = args.title
    if args.layout:
        creator.config.layout_preference = args.layout
    if args.style:
        creator.config.style = args.style
    if args.output:
        creator.config.output_formats = args.output
    if args.feishu_token:
        creator.config.feishu_doc_token = args.feishu_token
    
    # 生成相册
    result = creator.generate_complete_album(interactive=args.interactive)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result["status"] == "success":
        print(f"\n✅ 电子相册生成成功！")
        print(f"   标题: {result['config']['title']}")
        print(f"   图片数量: {result['processed_images_count']}")
        print(f"   页面数量: {result['generated_pages_count']}")
        print(f"   输出格式: {', '.join(result['config']['output_formats'])}")
    else:
        print(f"\n❌ 电子相册生成失败: {result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    from datetime import datetime
    main()