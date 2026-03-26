#!/usr/bin/env python3
"""
需求收集模块
负责收集用户对电子相册的具体需求
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class UserRequirements:
    """用户需求数据类"""
    # 基本需求
    image_paths: List[str] = None
    album_title: str = "我的电子相册"
    album_author: str = "用户"
    
    # 排版需求
    layout_preference: str = "mixed"  # single, two, three, four, mixed
    page_count: Optional[int] = None
    chapters: List[str] = None
    
    # 风格需求
    style: str = "elegant"  # elegant, simple, lively, business
    color_scheme: str = "default"
    font_preference: str = "default"
    
    # 文字需求
    need_text: bool = True
    text_amount: str = "moderate"  # minimal, moderate, detailed
    captions: Dict[str, str] = None  # 图片说明文字
    
    # 输出需求
    output_formats: List[str] = None  # feishu, pdf, images
    feishu_doc_token: Optional[str] = None
    
    # 特殊需求
    special_requirements: str = ""
    
    def __post_init__(self):
        if self.image_paths is None:
            self.image_paths = []
        if self.chapters is None:
            self.chapters = []
        if self.captions is None:
            self.captions = {}
        if self.output_formats is None:
            self.output_formats = ["feishu", "pdf"]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserRequirements':
        """从字典创建"""
        return cls(**data)


class RequirementCollector:
    """需求收集器"""
    
    def __init__(self, interactive_mode: bool = True):
        """
        初始化需求收集器
        
        Args:
            interactive_mode: 是否使用交互式收集
        """
        self.interactive_mode = interactive_mode
        self.requirements = UserRequirements()
        logger.info("需求收集器初始化完成")
    
    def collect_interactively(self) -> Dict[str, Any]:
        """
        交互式收集用户需求
        
        Returns:
            收集到的需求字典
        """
        logger.info("开始交互式需求收集")
        
        print("\n" + "="*50)
        print("电子相册需求收集")
        print("="*50)
        
        # 收集基本需求
        self._collect_basic_requirements()
        
        # 收集图片信息
        self._collect_image_info()
        
        # 收集排版需求
        self._collect_layout_requirements()
        
        # 收集风格需求
        self._collect_style_requirements()
        
        # 收集输出需求
        self._collect_output_requirements()
        
        # 收集特殊需求
        self._collect_special_requirements()
        
        # 显示汇总
        self._show_summary()
        
        # 确认需求
        if self._confirm_requirements():
            logger.info("需求收集完成并确认")
            return self.requirements.to_dict()
        else:
            logger.info("用户取消需求收集")
            return {}
    
    def collect_from_config(self, config_file: str) -> Dict[str, Any]:
        """
        从配置文件收集需求
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            收集到的需求字典
        """
        logger.info(f"从配置文件收集需求: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.requirements = UserRequirements.from_dict(config_data)
            logger.info("配置文件加载成功")
            return self.requirements.to_dict()
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return {}
    
    def collect_from_cli_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        从命令行参数收集需求
        
        Args:
            args: 命令行参数字典
            
        Returns:
            收集到的需求字典
        """
        logger.info("从命令行参数收集需求")
        
        # 更新需求
        if 'images' in args:
            self.requirements.image_paths = args['images']
        if 'title' in args:
            self.requirements.album_title = args['title']
        if 'layout' in args:
            self.requirements.layout_preference = args['layout']
        if 'style' in args:
            self.requirements.style = args['style']
        if 'output' in args:
            self.requirements.output_formats = args['output']
        
        logger.info("命令行参数收集完成")
        return self.requirements.to_dict()
    
    def _collect_basic_requirements(self):
        """收集基本需求"""
        print("\n📝 基本需求")
        print("-" * 30)
        
        # 相册标题
        title = input("1. 请输入相册标题（默认：我的电子相册）: ").strip()
        if title:
            self.requirements.album_title = title
        
        # 作者
        author = input("2. 请输入作者（默认：用户）: ").strip()
        if author:
            self.requirements.album_author = author
        
        # 预期页数
        page_count = input("3. 预期页数（可选，按回车跳过）: ").strip()
        if page_count and page_count.isdigit():
            self.requirements.page_count = int(page_count)
    
    def _collect_image_info(self):
        """收集图片信息"""
        print("\n🖼️ 图片信息")
        print("-" * 30)
        
        # 图片路径
        print("请提供图片文件路径（支持多个，用空格分隔）:")
        print("示例: /path/to/image1.jpg /path/to/image2.jpg")
        
        while True:
            image_input = input("图片路径: ").strip()
            if not image_input:
                print("⚠️ 必须提供至少一张图片")
                continue
            
            # 解析图片路径
            image_paths = image_input.split()
            valid_paths = []
            
            for path in image_paths:
                if os.path.exists(path):
                    valid_paths.append(path)
                else:
                    print(f"⚠️ 文件不存在: {path}")
            
            if valid_paths:
                self.requirements.image_paths = valid_paths
                print(f"✅ 找到 {len(valid_paths)} 张有效图片")
                break
            else:
                print("❌ 没有找到有效图片，请重新输入")
        
        # 章节划分（可选）
        print("\n是否需要划分章节？（按回车跳过）")
        chapters_input = input("章节名称（用逗号分隔）: ").strip()
        if chapters_input:
            chapters = [chap.strip() for chap in chapters_input.split(',')]
            self.requirements.chapters = chapters
            print(f"✅ 设置 {len(chapters)} 个章节")
    
    def _collect_layout_requirements(self):
        """收集排版需求"""
        print("\n📐 排版需求")
        print("-" * 30)
        
        print("请选择排版偏好:")
        print("1. 单张图片（每页一张，突出展示）")
        print("2. 两张图片（每页两张，对比展示）")
        print("3. 三张图片（每页三张，系列展示）")
        print("4. 四张图片（每页四张，密集展示）")
        print("5. 混合排版（自动选择最佳排版）")
        
        layout_map = {
            "1": "single",
            "2": "two", 
            "3": "three",
            "4": "four",
            "5": "mixed"
        }
        
        while True:
            choice = input("请选择（1-5，默认5）: ").strip()
            if not choice:
                choice = "5"
            
            if choice in layout_map:
                self.requirements.layout_preference = layout_map[choice]
                print(f"✅ 选择排版: {self.requirements.layout_preference}")
                break
            else:
                print("❌ 无效选择，请重新输入")
    
    def _collect_style_requirements(self):
        """收集风格需求"""
        print("\n🎨 风格需求")
        print("-" * 30)
        
        print("请选择相册风格:")
        print("1. 优雅风格（适合正式场合）")
        print("2. 简约风格（干净简洁）")
        print("3. 活泼风格（色彩鲜艳）")
        print("4. 商务风格（专业正式）")
        
        style_map = {
            "1": "elegant",
            "2": "simple",
            "3": "lively",
            "4": "business"
        }
        
        while True:
            choice = input("请选择（1-4，默认1）: ").strip()
            if not choice:
                choice = "1"
            
            if choice in style_map:
                self.requirements.style = style_map[choice]
                print(f"✅ 选择风格: {self.requirements.style}")
                break
            else:
                print("❌ 无效选择，请重新输入")
        
        # 文字需求
        print("\n📝 文字需求")
        print("1. 少量文字（仅标题）")
        print("2. 适中文字（标题+简短说明）")
        print("3. 详细文字（标题+详细描述）")
        
        text_map = {
            "1": "minimal",
            "2": "moderate",
            "3": "detailed"
        }
        
        while True:
            choice = input("请选择文字量（1-3，默认2）: ").strip()
            if not choice:
                choice = "2"
            
            if choice in text_map:
                self.requirements.text_amount = text_map[choice]
                print(f"✅ 选择文字量: {self.requirements.text_amount}")
                break
            else:
                print("❌ 无效选择，请重新输入")
    
    def _collect_output_requirements(self):
        """收集输出需求"""
        print("\n📤 输出需求")
        print("-" * 30)
        
        print("请选择输出格式（可多选，用空格分隔）:")
        print("1. 飞书文档（在线预览和编辑）")
        print("2. PDF文件（适合打印和分享）")
        print("3. 图片集合（所有页面单独保存）")
        
        format_map = {
            "1": "feishu",
            "2": "pdf",
            "3": "images"
        }
        
        while True:
            choices_input = input("请选择（1-3，默认1 2）: ").strip()
            if not choices_input:
                choices_input = "1 2"
            
            choices = choices_input.split()
            selected_formats = []
            
            for choice in choices:
                if choice in format_map:
                    selected_formats.append(format_map[choice])
                else:
                    print(f"⚠️ 忽略无效选项: {choice}")
            
            if selected_formats:
                self.requirements.output_formats = selected_formats
                print(f"✅ 选择输出格式: {', '.join(selected_formats)}")
                break
            else:
                print("❌ 没有选择有效格式，请重新输入")
        
        # 如果需要飞书文档，收集token
        if "feishu" in self.requirements.output_formats:
            token = input("请输入飞书文档token（可选，按回车跳过）: ").strip()
            if token:
                self.requirements.feishu_doc_token = token
                print("✅ 飞书token已设置")
            else:
                print("⚠️ 未提供飞书token，飞书文档生成可能受限")
    
    def _collect_special_requirements(self):
        """收集特殊需求"""
        print("\n🌟 特殊需求")
        print("-" * 30)
        
        print("是否有特殊需求？（按回车跳过）")
        print("例如：特定颜色、特殊字体、自定义模板等")
        
        special = input("特殊需求: ").strip()
        if special:
            self.requirements.special_requirements = special
            print("✅ 特殊需求已记录")
    
    def _show_summary(self):
        """显示需求汇总"""
        print("\n" + "="*50)
        print("需求汇总")
        print("="*50)
        
        req = self.requirements
        
        print(f"📖 相册标题: {req.album_title}")
        print(f"👤 作者: {req.album_author}")
        print(f"🖼️ 图片数量: {len(req.image_paths)} 张")
        
        if req.page_count:
            print(f"📄 预期页数: {req.page_count} 页")
        
        if req.chapters:
            print(f"📑 章节: {', '.join(req.chapters)}")
        
        print(f"📐 排版偏好: {req.layout_preference}")
        print(f"🎨 风格: {req.style}")
        print(f"📝 文字量: {req.text_amount}")
        print(f"📤 输出格式: {', '.join(req.output_formats)}")
        
        if req.special_requirements:
            print(f"🌟 特殊需求: {req.special_requirements}")
        
        print("="*50)
    
    def _confirm_requirements(self) -> bool:
        """确认需求"""
        while True:
            confirm = input("\n是否确认以上需求？（y/n）: ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                return True
            elif confirm in ['n', 'no', '否']:
                # 提供修改选项
                modify = input("是否修改需求？（y/n）: ").strip().lower()
                if modify in ['y', 'yes', '是']:
                    # 重新收集
                    return False
                else:
                    return False
            else:
                print("❌ 请输入 y/n 或 是/否")
    
    def save_requirements(self, filepath: str = "requirements.json"):
        """保存需求到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.requirements.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"需求已保存到 {filepath}")
            return True
        except Exception as e:
            logger.error(f"需求保存失败: {e}")
            return False
    
    def load_requirements(self, filepath: str = "requirements.json"):
        """从文件加载需求"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.requirements = UserRequirements.from_dict(data)
            logger.info(f"需求已从 {filepath} 加载")
            return True
        except Exception as e:
            logger.error(f"需求加载失败: {e}")
            return False


def main():
    """命令行测试"""
    collector = RequirementCollector()
    requirements = collector.collect_interactively()
    
    if requirements:
        print("\n✅ 需求收集成功！")
        print(json.dumps(requirements, ensure_ascii=False, indent=2))
        
        # 保存需求
        collector.save_requirements()
    else:
        print("\n❌ 需求收集取消")


if __name__ == "__main__":
    main()