import pandas as pd
import networkx as nx
import os
import json
import re
from tqdm import tqdm

# --- 1. 路径配置 ---
path = r"E:\课程资料\6-大三下\数字人文导论\漫威_v3\漫威_v2"
# 确保使用我们之前生成的战术数据库
db_path = os.path.join(path, "hero_tactical_v3.csv") 
network_path = os.path.join(path, "cleaned_hero_network.csv")
master_path = os.path.join(path, "hero_master_final.csv")
template_path = os.path.join(path, "game.html")
output_path = os.path.join(path, "game_rendered.html")

print("[Game] Starting S.H.I.E.L.D. tactical system (Matrix Engine)...")

# --- 2. 辅助函数：生成图片路径（已弃用，保留但不使用）---
def get_hero_img_path(eng_name):
    # 将 "IRON MAN/TONY STARK" 转为 "iron_man"
    clean_name = eng_name.split('/')[0].strip().lower().replace(' ', '_')
    clean_name = re.sub(r'[^\w]', '', clean_name)
    return f"./pic/heroes/{clean_name}.jpg"

# --- 2.1 辅助函数：解析 Modules_JSON 供步骤04滑块计算使用 ---
def parse_modules(modules_json_str):
    """解析 Modules_JSON 字段，提取 Tech/Diplomacy/Force 三个模块的权重"""
    default_module = {
        "name": "默认行动",
        "weights": {"order": 0, "cohesion": 0, "trust": 0},
        "target_cn": "无",
        "graph_impact": {"impact_pct": "0.01", "winner": "无", "loser": "无"}
    }
    try:
        modules = json.loads(modules_json_str)
        result = {}
        for key in ["Tech", "Diplomacy", "Force"]:
            if key in modules:
                m = modules[key]
                # 构建模块结构供前端实时计算
                result[key] = {
                    "name": m.get("name", key),
                    "weights": {
                        "order": m.get("order", 0),
                        "cohesion": m.get("cohesion", 0),
                        "trust": m.get("trust", 0)
                    },
                    "target_cn": m.get("impact_target", "无"),
                    "graph_impact": {"impact_pct": "0.01", "winner": "无", "loser": "无"}
                }
            else:
                result[key] = default_module.copy()
        return result
    except:
        return {"Tech": default_module.copy(), "Diplomacy": default_module.copy(), "Force": default_module.copy()}

# --- 3. 加载基础数据 ---
if not os.path.exists(db_path):
    print(f"[ERROR] File not found: {db_path}.")
    exit()

tac_df = pd.read_csv(db_path)
master_df = pd.read_csv(master_path)
edges_df = pd.read_csv(network_path)

# 构建全量社交网络（6000+人）
G_base = nx.from_pandas_edgelist(edges_df, 'hero1', 'hero2')
print("[Game] Scanning current power status (PageRank)...")
base_pagerank = nx.pagerank(G_base, max_iter=50)
name_map = dict(zip(master_df['English_Name'], master_df['Chinese_Name']))

# --- 新增：构建英文名 -> Image_URL 的映射（与第二套代码逻辑一致）---
img_map = dict(zip(master_df['English_Name'], master_df['Image_URL']))

# --- 4. 核心演算逻辑 ---
game_db = {}
print(f"[Game] Simulating tactical decisions for {len(tac_df)} heroes...")

for _, row in tqdm(tac_df.iterrows(), total=len(tac_df)):
    hero_eng = row['English_Name']
    hero_cn = row['Chinese_Name']
    
    # --- 新增：图片 URL 处理（完全模仿第二套代码）---
    img_url = img_map.get(hero_eng, './pic/shield_logo.webp')
    if pd.isna(img_url) or str(img_url).strip() == '':
        img_url = './pic/shield_logo.webp'
    # 将反斜杠转为正斜杠
    img_url = str(img_url).replace('\\', '/')
    # 确保路径以 ./ 开头（相对路径）
    if not img_url.startswith('./') and not img_url.startswith('http'):
        img_url = './' + img_url
    
    # 解析 Modules_JSON 字段获取两个行动
    processed_results = {}
    try:
        modules_json = json.loads(row['Modules_JSON'])
        # 获取前两个行动
        action_keys = list(modules_json.keys())[:2]
        for i, key in enumerate(action_keys):
            module = modules_json[key]
            action_label = module.get('name', key)
            impact_target = module.get('impact_target', '')
            op = 'add' if module.get('order', 0) > 0 else 'remove'
            
            G_sim = G_base.copy()
            target = impact_target
            
            # 修改网络结构
            if target and G_sim.has_node(hero_eng) and G_sim.has_node(target):
                if op == 'remove' and G_sim.has_edge(hero_eng, target):
                    G_sim.remove_edge(hero_eng, target)
                elif op == 'add':
                    G_sim.add_edge(hero_eng, target)
                    
                # 1. 计算宇宙凝聚力损毁度
                size_new = len(max(nx.connected_components(G_sim), key=len))
                impact_val = round((6399 - size_new) / 63.99, 4)
                
                # 2. 计算权力大洗牌 (PageRank 变化)
                new_pr = nx.pagerank(G_sim, max_iter=30, tol=1e-04)
                diff = {n: new_pr[n] - base_pagerank.get(n, 0) for n in new_pr if n in base_pagerank}
                if hero_eng in diff: del diff[hero_eng]
                
                winner_eng = max(diff, key=diff.get) if diff else hero_eng
                loser_eng = min(diff, key=diff.get) if diff else hero_eng
                
                processed_results[key] = {
                    "label": action_label,
                    "impact_pct": impact_val if impact_val > 0.01 else "0.01",
                    "winner": name_map.get(winner_eng, winner_eng),
                    "loser": name_map.get(loser_eng, loser_eng)
                }
    except Exception as e:
        # 如果解析失败，使用默认数据
        processed_results = {
            "Tech": {"label": "科技干预", "impact_pct": "0.01", "winner": "美国队长", "loser": "钢铁侠"}
        }
    
    # 封存档案数据
    game_db[hero_cn] = {
        "name": hero_cn,
        "eng": hero_eng,
        "motto_tags": str(row['Motto']).split('|'),
        "spec_tags": str(row['Spec']).split('|'),
        "limit_tags": str(row['Limit']).split('|'),
        "coords": {"x": float(row['X']), "y": float(row['Y'])},
        "context": row['Scenario'],
        "effects": processed_results,
        "audit_pos": str(row['Evaluation'])[:100] if pd.notna(row['Evaluation']) else "",
        "audit_neg": "",
        "img": img_url,   # 修改：使用从 CSV 读取并清洗后的 URL
        # 新增：完整解析 Modules_JSON 供步骤04滑块计算使用
        "modules": parse_modules(row['Modules_JSON'])
    }

# --- 5. 注入 HTML ---
print("[Game] Injecting tactical data into HTML...")
try:
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 注入 JSON 数据
    html_content = html_content.replace('{{ hero_game_json }}', json.dumps(game_db, ensure_ascii=False))
    
    # 注入一个随机 ID 模拟档案编号
    import random
    html_content = html_content.replace('{{ random_id }}', str(random.randint(10000, 99999)))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("-" * 30)
    print("[OK] Echo Project completed!")
    print(f"Output: {output_path}")

except Exception as e:
    print(f"[ERROR] Injection failed: {e}")