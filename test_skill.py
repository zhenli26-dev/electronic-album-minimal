#!/usr/bin/env python3
"""
电子相册Skill测试脚本
用于验证所有模块功能是否正常
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加scripts目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def test_module_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    modules_to_test = [
        'collect_requirements',
        'process_images',
        'apply_templates',
        'generate_output',
        'main_workflow'
    ]
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name}.py - 导入成功")
        except ImportError as e:
            print(f"  ❌ {module_name}.py - 导入失败: {e}")
            return False
    
    print("✅ 所有模块导入测试通过")
    return True

def test_dependencies():
    """测试依赖包"""
    print("\n🔍 测试依赖包...")
    
    dependencies = [
        ('PIL', 'Pillow'),
        ('img2pdf', 'img2pdf'),
    ]
    
    for import_name, package_name in dependencies:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name} - 已安装")
        except ImportError:
            print(f"  ❌ {package_name} - 未安装")
            print(f"     请运行: pip install {package_name}")
            return False
    
    print("✅ 所有依赖包测试通过")
    return True

def test_template_files():
    """测试模板文件"""
    print("\n🔍 测试模板文件...")
    
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    required_templates = [
        '01_cover.jpg',
        '02_directory.jpg',
        '03_single_image.jpg',
        '04_two_images.jpg',
        '05_three_images.jpg',
        '06_four_images.md',
        'template_index.md'
    ]
    
    missing_templates = []
    
    for template in required_templates:
        template_path = os.path.join(templates_dir, template)
        if os.path.exists(template_path):
            print(f"  ✅ {template} - 存在")
        else:
            print(f"  ❌ {template} - 缺失")
            missing_templates.append(template)
    
    if missing_templates:
        print(f"❌ 缺失模板文件: {missing_templates}")
        return False
    
    print("✅ 所有模板文件测试通过")
    return True

def test_skill_structure():
    """测试Skill结构"""
    print("\n🔍 测试Skill结构...")
    
    required_dirs = [
        'scripts',
        'templates',
        'examples',
        'references'
    ]
    
    required_files = [
        'SKILL.md',
        'INSTALL.md',
        'requirements.txt',
        'test_skill.py'
    ]
    
    skill_dir = os.path.dirname(__file__)
    
    # 检查目录
    for dir_name in required_dirs:
        dir_path = os.path.join(skill_dir, dir_name)
        if os.path.isdir(dir_path):
            print(f"  ✅ {dir_name}/ - 目录存在")
        else:
            print(f"  ❌ {dir_name}/ - 目录缺失")
            return False
    
    # 检查文件
    for file_name in required_files:
        file_path = os.path.join(skill_dir, file_name)
        if os.path.isfile(file_path):
            print(f"  ✅ {file_name} - 文件存在")
        else:
            print(f"  ❌ {file_name} - 文件缺失")
            return False
    
    print("✅ Skill结构测试通过")
    return True

def test_basic_functionality():
    """测试基本功能"""
    print("\n🔍 测试基本功能...")
    
    try:
        # 测试需求收集模块
        from collect_requirements import RequirementCollector
        collector = RequirementCollector()
        print("  ✅ RequirementCollector - 初始化成功")
        
        # 测试图片处理配置
        from process_images import ImageProcessingConfig, ImageProcessor
        config = ImageProcessingConfig()
        print("  ✅ ImageProcessingConfig - 创建成功")
        
        # 测试模板引擎配置
        from apply_templates import TemplateConfig, TemplateEngine
        template_config = TemplateConfig()
        print("  ✅ TemplateConfig - 创建成功")
        
        # 测试输出生成配置
        from generate_output import OutputConfig, OutputGenerator
        output_config = OutputConfig()
        print("  ✅ OutputConfig - 创建成功")
        
        print("✅ 基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def create_test_images():
    """创建测试图片"""
    print("\n🔍 创建测试图片...")
    
    try:
        from PIL import Image, ImageDraw
        
        # 创建临时目录
        test_dir = tempfile.mkdtemp(prefix="album_test_")
        print(f"  测试目录: {test_dir}")
        
        # 创建3张测试图片
        test_images = []
        for i in range(3):
            img_path = os.path.join(test_dir, f"test_image_{i+1}.jpg")
            
            # 创建简单图片
            img = Image.new('RGB', (800, 600), color=(i*50, 100, 150))
            draw = ImageDraw.Draw(img)
            
            # 添加文字
            draw.text((100, 100), f"测试图片 {i+1}", fill=(255, 255, 255))
            draw.text((100, 150), "电子相册Skill测试", fill=(255, 255, 255))
            
            img.save(img_path, quality=90)
            test_images.append(img_path)
            
            print(f"  ✅ 创建测试图片: {os.path.basename(img_path)}")
        
        return test_dir, test_images
        
    except Exception as e:
        print(f"❌ 创建测试图片失败: {e}")
        return None, []

def test_integration():
    """测试集成功能"""
    print("\n🔍 测试集成功能...")
    
    test_dir, test_images = create_test_images()
    if not test_images:
        return False
    
    try:
        # 创建输出目录
        output_dir = os.path.join(test_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 测试图片处理
        from process_images import ImageProcessor
        processor = ImageProcessor()
        
        processed_dir = os.path.join(test_dir, "processed")
        processed_images = processor.batch_process(test_images, processed_dir)
        
        if processed_images:
            print(f"  ✅ 图片处理成功: {len(processed_images)}张")
        else:
            print("  ❌ 图片处理失败")
            return False
        
        # 测试模板应用
        from apply_templates import TemplateEngine, TemplateType
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        engine = TemplateEngine(templates_dir)
        
        # 创建测试页面
        from apply_templates import AlbumPage
        test_page = AlbumPage(
            page_number=1,
            template_type=TemplateType.SINGLE,
            images=[processed_images[0]],
            captions=["测试图片1"],
            title="测试页面"
        )
        
        page_output = engine.apply_template(test_page, output_dir)
        if page_output and os.path.exists(page_output):
            print(f"  ✅ 模板应用成功: {os.path.basename(page_output)}")
        else:
            print("  ❌ 模板应用失败")
            return False
        
        # 清理测试目录
        shutil.rmtree(test_dir)
        print(f"  ✅ 清理测试目录: {test_dir}")
        
        print("✅ 集成功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 集成功能测试失败: {e}")
        
        # 清理测试目录
        if test_dir and os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
                print(f"  已清理测试目录: {test_dir}")
            except:
                pass
        
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("电子相册Skill测试套件")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_module_imports),
        ("依赖包", test_dependencies),
        ("模板文件", test_template_files),
        ("Skill结构", test_skill_structure),
        ("基本功能", test_basic_functionality),
        ("集成功能", test_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 打印汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:20} {status}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"总计: {passed}/{total} 项测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！电子相册Skill功能正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total-passed} 项测试失败，请检查上述问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())