import os
import pandas as pd
import glob
import re
import json

# ==================== 1. 路径配置 ====================
path = r"E:\课程资料\6-大三下\数字人文导论\marvel-project"
CSV_PATH = os.path.join(path, "hero_master_final.csv")
PIC_DIR = os.path.join(path, "pic", "heroes")

print("🔍 [系统启动] 正在进行全量图像逻辑重组...")

# ==================== 2. 核心去噪函数 ====================
def simplify(text):
    """只保留大写字母和数字，彻底抹平空格、下划线、括号、斜杠"""
    if pd.isna(text): return ""
    return re.sub(r'[^A-Z0-9]', '', str(text).upper())

def main():
    # 1. 扫描图片文件夹
    image_files = glob.glob(os.path.join(PIC_DIR, "*.jpg"))
    if not image_files:
        print(f"❌ 错误：在 {PIC_DIR} 下没找到任何 .jpg 文件！")
        return

    # 建立【纯净指纹】到【实际文件名】的映射
    # 例如：'SPIDERMANPETERPAR' -> 'SPIDER-MAN_PETER PAR.jpg'
    file_fingerprints = {}
    for f in image_files:
        raw_name = os.path.splitext(os.path.basename(f))[0]
        file_fingerprints[simplify(raw_name)] = os.path.basename(f)
    
    print(f"📊 发现 {len(image_files)} 张英雄照片。")

    # 2. 读取核心数据库
    df = pd.read_csv(CSV_PATH)
    
    # 3. 执行“模糊穿透”匹配算法
    def find_hero_image(hero_name):
        naked_hero = simplify(hero_name)
        if not naked_hero: return "pic/shield_logo.webp"

        # 策略 A：指纹完全吻合
        if naked_hero in file_fingerprints:
            return f"pic/heroes/{file_fingerprints[naked_hero]}"

        # 策略 B：处理 20 字符截断 (最核心的修复)
        # 只要 CSV 名的前 12 位能对上文件名的前 12 位
        hero_prefix = naked_hero[:12]
        for f_naked, f_real in file_fingerprints.items():
            if f_naked.startswith(hero_prefix) or hero_prefix.startswith(f_naked[:10]):
                return f"pic/heroes/{f_real}"
        
        # 策略 C：处理包含关系（针对名字里有括号或逗号的情况）
        for f_naked, f_real in file_fingerprints.items():
            if len(f_naked) > 5 and (f_naked in naked_hero or naked_hero in f_naked):
                return f"pic/heroes/{f_real}"

        return "pic/shield_logo.webp"

    print("🧠 正在匹配 496 名英雄的视觉资料...")
    df['Image_URL'] = df['English_Name'].apply(find_hero_image)

    # 4. 统计结果
    matched = df[df['Image_URL'] != "pic/shield_logo.webp"]
    success_count = len(matched)
    
    # 5. 覆盖保存 CSV
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    print(f"✅ 匹配成功：{success_count} / {len(df)}")
    
    if success_count > 1:
        print("\n📝 抽样验证成功案例：")
        for _, r in matched.head(5).iterrows():
            print(f"   - {r['English_Name']}  -->  {r['Image_URL']}")
    else:
        print("\n❌ 依然只有极少数匹配。请手动检查一张图片的【完整文件名】。")

if __name__ == "__main__":
    main()