"""
字体解析工具模块

该模块提供了从WOFF/TTF字体文件中提取字符映射关系的功能。
主要通过将字体字符渲染为图像，然后使用OCR识别来实现字体反爬虫的破解。
"""

from fontTools.ttLib import TTFont
import ddddocr
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, Optional
import os
import logging
from functools import lru_cache

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def convert_cmap_to_image(cmap_code: int, font_path: str, img_size: int = 1024) -> Image.Image:
    """
    将Unicode码点转换为对应字符的图像
    
    Args:
        cmap_code: Unicode码点
        font_path: 字体文件路径
        img_size: 生成图像的大小
        
    Returns:
        PIL.Image对象，包含渲染的字符
        
    Raises:
        FileNotFoundError: 字体文件不存在
        ValueError: Unicode码点无效
    """
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"字体文件不存在: {font_path}")

    if cmap_code < 0:
        raise ValueError(f"无效的Unicode码点: {cmap_code}")

    # 创建一个临时的大图像，用于计算实际字符尺寸
    temp_size = img_size * 2  # 创建一个更大的临时图像
    temp_img = Image.new("1", (temp_size, temp_size), 255)
    temp_draw = ImageDraw.Draw(temp_img)

    try:
        font = ImageFont.truetype(font_path, img_size)
    except Exception as e:
        raise ValueError(f"无法加载字体文件: {e}")

    # 将 cmap code 转换为字符
    character = chr(cmap_code)

    # 在临时图像中心绘制文本
    temp_center = temp_size // 2
    temp_draw.text(
        (temp_center, temp_center),
        character,
        font=font,
        anchor="mm"  # 使用锚点参数，以字符中心点为准进行定位
    )

    # 裁剪非空白区域
    bbox = temp_img.getbbox()
    if bbox:
        # 确保有足够的边距
        padding = img_size // 10
        left, top, right, bottom = bbox
        width = right - left
        height = bottom - top

        # 计算新的裁剪区域，确保居中
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2

        # 确保裁剪区域是正方形
        half_size = max(width, height) // 2 + padding
        crop_left = max(0, center_x - half_size)
        crop_top = max(0, center_y - half_size)
        crop_right = min(temp_size, center_x + half_size)
        crop_bottom = min(temp_size, center_y + half_size)

        # 裁剪图像
        cropped_img = temp_img.crop((crop_left, crop_top, crop_right, crop_bottom))

        # 调整到最终尺寸
        final_img = cropped_img.resize((img_size, img_size), Image.LANCZOS)
    else:
        # 如果没有找到边界框，返回原始图像
        final_img = Image.new("1", (img_size, img_size), 255)

    final_img.save(f"./imgs/{cmap_code}.png",'PNG')
    return final_img


def extract_text_from_font(
        font_path: str,
        image_size: int = 1024,
        show_progress: bool = False,
        use_cache: bool = True,
        cache_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    从字体文件中提取字符映射关系
    
    Args:
        font_path: 字体文件路径
        image_size: 生成图像的大小
        show_progress: 是否显示进度信息
        use_cache: 是否使用缓存来提高相同字体的处理速度
        cache_dir: 缓存目录，如果为None则不保存图像
        
    Returns:
        字典，键为字体中的glyph名称，值为OCR识别结果
        
    Raises:
        FileNotFoundError: 字体文件不存在
        ValueError: 字体文件格式错误
    """
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"字体文件不存在: {font_path}")

    # 创建缓存目录
    if cache_dir and not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    try:
        # 加载字体文件
        font = TTFont(font_path)
        # 获取最佳的字符映射表
        cmap = font.getBestCmap()
    except Exception as e:
        raise ValueError(f"无法解析字体文件: {e}")

    # 图像识别模块：DdddOcr
    ocr = ddddocr.DdddOcr(beta=True, show_ad=False)

    font_map = {}
    total_chars = len(cmap)

    for idx, (cmap_code, glyph_name) in enumerate(cmap.items()):
        if show_progress and idx % max(1, total_chars // 10) == 0:
            logger.info(f"处理进度: {idx}/{total_chars} ({idx / total_chars * 100:.1f}%)")

        try:
            # 将字体字符转换为图像
            image = convert_cmap_to_image(cmap_code, font_path, image_size)

            # 保存图像到缓存（如果启用）
            if cache_dir:
                character = chr(cmap_code)
                cache_path = os.path.join(cache_dir, f"{ord(character)}_{glyph_name}.png")
                if not os.path.exists(cache_path):
                    image.save(cache_path, "PNG")

            # 提取图像字符
            bytes_io = BytesIO()
            image.save(bytes_io, "PNG")
            text = ocr.classification(bytes_io.getvalue())

            # 存储映射关系
            font_map[glyph_name] = text

        except Exception as e:
            logger.warning(f"处理字符时出错 (码点: {cmap_code}, 名称: {glyph_name}): {e}")
            font_map[glyph_name] = ""  # 出错时使用空字符串

    if show_progress:
        logger.info(f"处理完成: 共 {total_chars} 个字符")

    return font_map


def get_font_info(font_path: str) -> Tuple[Dict, Dict]:
    """
    获取字体文件的基本信息
    
    Args:
        font_path: 字体文件路径
        
    Returns:
        包含字体信息的元组 (字体名称和信息字典, 码点映射字典)
    """
    font = TTFont(font_path)

    # 提取字体信息
    font_info = {}
    if 'name' in font:
        for record in font['name'].names:
            if record.isUnicode():
                key = record.nameID
                value = record.toUnicode()
                font_info[key] = value

    # 获取字符映射
    cmap = font.getBestCmap()

    return font_info, cmap


"""
使用示例文档
===========

本模块主要用于处理字体反爬虫中常见的字体映射问题。
以下是各函数的详细使用示例。

"""

if __name__ == "__main__":
    """
    以下是模块的使用示例
    """


    # 示例1：基本的字体解析
    def basic_usage_example():
        """
        基本使用示例 - 从字体文件中提取文字映射
        """
        print("=== 基本字体解析示例 ===")
        font_path = "./fonts/example.woff"  # 字体文件路径

        try:
            # 提取字体映射
            font_map = extract_text_from_font(font_path, show_progress=True)

            # 打印部分映射结果
            print(f"共解析出 {len(font_map)} 个字符映射")
            sample_items = list(font_map.items())[:10]  # 取前10个作为样例
            for glyph, text in sample_items:
                print(f"字形名称: {glyph} -> 识别文本: {text}")

        except Exception as e:
            print(f"解析失败: {e}")


    # 示例2：将解析结果用于实际页面解密
    def decrypt_webpage_example():
        """
        实际应用示例 - 用于解密网页中的字体加密内容
        """
        print("\n=== 网页内容解密示例 ===")

        # 假设这是从网页中提取的字体文件和加密文本
        font_path = "./fonts/encrypted.woff"
        encrypted_text = "&#xe78c;&#xe562;&#xe3d9;&#xe671;"  # 加密后的文本

        try:
            # 1. 解析字体映射
            font_map = extract_text_from_font(
                font_path,
                image_size=512,  # 较小的图像尺寸可提高速度
                show_progress=True,
                cache_dir="./font_cache"  # 使用缓存加速后续解析
            )

            # 2. 将网页中的加密文本转换为实际文本
            # 假设网页中使用的是形如 &#xe78c; 的格式
            result = ""
            for part in encrypted_text.split(";"):
                if not part:
                    continue

                # 提取十六进制码点
                hex_code = part.replace("&#x", "")
                if not hex_code:
                    continue

                # 查找对应的文本
                unicode_name = f"uni{hex_code.upper()}"
                if unicode_name in font_map:
                    result += font_map[unicode_name]
                else:
                    result += "?"  # 未识别的字符

            print(f"原始加密文本: {encrypted_text}")
            print(f"解密后文本: {result}")

        except Exception as e:
            print(f"解密失败: {e}")


    # 示例3：字体信息获取
    def font_info_example():
        """
        获取字体基本信息的示例
        """
        print("\n=== 字体信息获取示例 ===")
        font_path = "./fonts/example.woff"

        try:
            font_info, cmap = get_font_info(font_path)

            print("字体基本信息:")
            # 常见的nameID含义:
            # 1: 字体家族名称, 2: 字体子系列, 4: 完整名称, 6: PostScript名称
            name_id_meanings = {
                1: "字体家族名称",
                2: "字体子系列",
                4: "完整名称",
                6: "PostScript名称"
            }

            for name_id, value in font_info.items():
                meaning = name_id_meanings.get(name_id, "其他信息")
                print(f"  - {meaning} ({name_id}): {value}")

            print(f"\n字体包含字符数: {len(cmap)}")
            # 打印部分字符码点
            sample_chars = list(cmap.items())[:5]
            for code, name in sample_chars:
                print(f"  - Unicode: U+{code:04X}, 字符: {chr(code)}, 名称: {name}")

        except Exception as e:
            print(f"获取字体信息失败: {e}")


    # 示例4：批量处理多个字体
    def batch_processing_example():
        """
        批量处理多个字体文件的示例
        """
        print("\n=== 批量处理字体示例 ===")
        font_dir = "./fonts/"

        # 获取目录中的所有woff/ttf文件
        import glob
        font_files = glob.glob(f"{font_dir}*.woff") + glob.glob(f"{font_dir}*.ttf")

        print(f"发现 {len(font_files)} 个字体文件")

        for i, font_path in enumerate(font_files, 1):
            print(f"\n处理字体 {i}/{len(font_files)}: {os.path.basename(font_path)}")
            try:
                # 获取字体信息
                font_info, _ = get_font_info(font_path)
                font_name = font_info.get(4, os.path.basename(font_path))

                # 解析字体
                font_map = extract_text_from_font(
                    font_path,
                    show_progress=False,
                    cache_dir=f"./font_cache/{os.path.basename(font_path).split('.')[0]}"
                )

                print(f"  - 字体名称: {font_name}")
                print(f"  - 映射字符数: {len(font_map)}")

            except Exception as e:
                print(f"  - 处理失败: {e}")


    # 运行示例函数
    # basic_usage_example()
    # decrypt_webpage_example()
    # font_info_example()
    # batch_processing_example()

    print("\n要运行示例，请取消注释上方的示例函数调用")

"""
注意事项与最佳实践
==============

1. 性能优化:
   - 对于大型字体文件，可使用较小的image_size来提高处理速度
   - 使用cache_dir参数缓存图像，避免重复处理相同字体
   
2. 准确率提升:
   - 如果OCR识别不准确，可尝试调整图像大小
   - 对于特定网站，可能需要手动校正部分映射结果
   
3. 错误处理:
   - 始终使用try-except包裹字体处理代码，以防字体文件损坏
   - 对于无法识别的字符，提供合理的默认值或提示

4. 实际应用:
   - 在爬虫中，通常结合requests和BeautifulSoup使用本模块
   - 对于动态变化的字体文件，需要实现自动下载和解析逻辑
   
示例应用场景:
1. 票务网站价格解密
2. 电商网站评分/评论解密
3. 文档分享网站内容解密
4. 房产网站价格信息解密
"""
