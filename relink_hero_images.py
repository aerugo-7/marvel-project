#!/usr/bin/env python3
"""
重新匹配英雄图片脚本 V2
功能：扫描图片目录，模糊匹配英雄名和图片名
未匹配的自动使用神盾局logo
"""
import os
import csv
import glob
import re

# 配置路径
CSV_PATH = os.path.join(os.path.dirname(__file__), "hero_master_final.csv")
PIC_DIR = os.path.join(os.path.dirname(__file__), "pic", "heroes")
SHIELD_LOGO = "pic/shield_logo.webp"

def standardize_for_match(name: str) -> str:
    """标准化处理用于匹配"""
    name = name.replace(" ", "").replace("_", "").replace("-", "").replace("(", "").replace(")", "")
    if "/" in name:
        name = name.split("/")[0]
    return name.upper()

def extract_core_name(hero_name: str) -> str:
    """提取核心名称用于模糊匹配"""
    # 移除常见前缀和后缀
    name = hero_name.upper()
    # 移除常见标题
    for prefix in ["DR.", "MR.", "MS.", "MISS ", "SIR ", "COL. ", "CAPTAIN ", "KING ", "QUEEN ", "LORD "]:
        name = name.replace(prefix, "")
    # 移除括号内容
    name = re.sub(r'\([^)]*\)', '', name)
    # 提取第一个单词作为核心
    core = name.split()[0] if name.split() else name
    return standardize_for_match(core)

def main():
    # 1. 扫描图片目录
    image_files = glob.glob(os.path.join(PIC_DIR, "*.jpg"))
    image_map = {}
    for img_path in image_files:
        filename = os.path.splitext(os.path.basename(img_path))[0]
        key = standardize_for_match(filename)
        image_map[key] = os.path.basename(img_path)
    
    print(f"[INFO] Found {len(image_files)} image files")
    print(f"[INFO] Image keys: {list(image_map.keys())[:10]}")
    
    # 2. 读取CSV - 移除BOM
    heroes_data = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            heroes_data.append(row)
    
    print(f"[INFO] CSV has {len(heroes_data)} hero records")
    
    # 3. 匹配并更新 - 优先精确匹配，然后模糊匹配
    matched_count = 0
    fuzzy_matched = 0
    unmatched_heroes = []
    matched_images_used = set()
    
    for hero in heroes_data:
        # 处理可能的BOM前缀
        hero_name = hero.get('\ufeffEnglish_Name') or hero.get('English_Name') or hero.get('hero', '')
        if not hero_name:
            continue
        
        hero_key = standardize_for_match(hero_name)
        matched = False
        
        # 精确匹配
        if hero_key in image_map and hero_key not in matched_images_used:
            hero['Image_URL'] = f"pic\\heroes\\{image_map[hero_key]}"
            matched = True
            matched_count += 1
            matched_images_used.add(hero_key)
        else:
            # 模糊匹配 - 提取核心名匹配
            core = extract_core_name(hero_name)
            for img_key, img_file in image_map.items():
                if core and core in img_key or img_key in core:
                    if img_key not in matched_images_used:
                        hero['Image_URL'] = f"pic\\heroes\\{img_file}"
                        matched = True
                        fuzzy_matched += 1
                        matched_images_used.add(img_key)
                        break
        
        if not matched:
            hero['Image_URL'] = f"pic\\{SHIELD_LOGO}"
            unmatched_heroes.append(hero_name)
    
    # 4. 写回CSV
    fieldnames = list(heroes_data[0].keys())
    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(heroes_data)
    
    print(f"\n[DONE] Matching complete!")
    print(f"   Exact match: {matched_count}")
    print(f"   Fuzzy match: {fuzzy_matched}")
    print(f"   Total matched: {matched_count + fuzzy_matched}/{len(heroes_data)}")
    print(f"   Using placeholder: {len(unmatched_heroes)}")
    
    if unmatched_heroes:
        print(f"\n[WARNING] Unmatched heroes (will use shield logo):")
        for h in unmatched_heroes[:20]:
            print(f"   - {h}")
        if len(unmatched_heroes) > 20:
            print(f"   ... and {len(unmatched_heroes) - 20} more")

if __name__ == "__main__":
    main()